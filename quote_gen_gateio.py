from typing import Dict, List, Tuple
import numpy as np
from orderbook_gateio import OrderbookGateio
from inventory_manager_gateio import InventoryManagerGateio
import asyncio
from features_gateio import FeaturesGateio

class ContractParams:
    def __init__(self, contract: str):
        self.contract = contract  # Identifier for the contract (e.g., "BTC_USDT")
        self.max_long = 100.0      # Maximum allowed long position size
        self.max_short = -100.0    # Maximum allowed short position size (negative value)
        self.current_position = 0.0  # Current position size, updated dynamically
        self.default_long_size = 10.0  # Default order size for long quotes
        self.default_short_size = 10.0  # Default order size for short quotes
        self.positive_quote_distance_bps = 10  # Distance in basis points above mid price for ask quotes
        self.negative_quote_distance_bps = 10  # Distance in basis points below mid price for bid quotes
        self.quote_step_size = 1  # Minimum increment for order size. ie round to this value. nearest integer in this case
        self.long_adjustment_threshold_bps = 5  # Threshold in basis points to trigger long quote update. ie if price diff of new quotes is greater than this value, update quote
        self.short_adjustment_threshold_bps = 5  # Threshold in basis points to trigger short quote update
        self.price_rounding_precision = 2  # Number of decimal places for rounding quoted prices. round prices to this many dp
        self.enable_long_quotes = True  # Flag to enable quoting on the buy side
        self.enable_short_quotes = True  # Flag to enable quoting on the sell side
        self.price_step = 0.01  # Minimum price increment for quotes

    def long_reduction_func(self) -> int:
        if self.current_position <= 0:
            size = self.default_long_size
        else:
            size = max(0, self.default_long_size * (1 - self.current_position / self.max_long))
        return round(size / self.quote_step_size) * self.quote_step_size

    def short_reduction_func(self) -> int:
        if self.current_position >= 0:
            size = self.default_short_size
        else:
            size = max(0, self.default_short_size * (1 + self.current_position / self.max_short))
        return -round(size / self.quote_step_size) * self.quote_step_size  # Negative for sells

    def update_position(self, new_position: float):
        self.current_position = new_position

    def set_quote_distances(self, positive_bps: float, negative_bps: float):
        self.positive_quote_distance_bps = positive_bps
        self.negative_quote_distance_bps = negative_bps

    def set_adjustment_thresholds(self, long_bps: float, short_bps: float):
        self.long_adjustment_threshold_bps = long_bps
        self.short_adjustment_threshold_bps = short_bps

    def set_price_rounding_precision(self, precision: int):
        self.price_rounding_precision = precision

    def set_enable_quotes(self, long: bool, short: bool):
        self.enable_long_quotes = long
        self.enable_short_quotes = short

    def set_price_step(self, step: float):
        self.price_step = step

class QuoteGenerator:
    def __init__(self, contracts: List[str], orderbook_depth: int = 20):
        self.contracts = contracts
        self.orderbook_manager = OrderbookGateio(contracts=contracts, size=orderbook_depth)
        self.orderbook_manager.on_update_callback = self.on_orderbook_update
        self.inventory_manager = InventoryManagerGateio()
        self.inventory_manager.on_position_update = self.on_position_update
        self.positions: Dict[str, float] = {contract: 0.0 for contract in contracts}
        self.contract_params: Dict[str, ContractParams] = {contract: ContractParams(contract) for contract in contracts}
        self.current_quotes: Dict[str, Dict[str, float]] = {contract: {'buy_price': 0, 'sell_price': 0, 'buy_size': 0, 'sell_size': 0} for contract in contracts}

    def on_orderbook_update(self, contract: str, bids: np.ndarray, asks: np.ndarray):
        self.generate_quotes(contract, bids[0][0], asks[0][0])

    def on_position_update(self, positions: List[Tuple[str, float]]):
        for contract, size in positions:
            if contract in self.positions:
                self.positions[contract] = size
                self.contract_params[contract].update_position(size)

    def generate_quotes(self, contract: str, best_bid: float, best_ask: float):
        params = self.contract_params[contract]
        current_position = self.positions[contract]

        new_buy_price = 0
        new_sell_price = 0
        new_buy_size = 0
        new_sell_size = 0

        mid_price = (best_bid + best_ask) / 2 ### not implemented properly. need to import features and quote vamp price

        new_buy_price = round(mid_price * (1 - params.negative_quote_distance_bps / 10000), params.price_rounding_precision)
        if new_buy_price >= best_bid:
            new_buy_price = round(best_bid - params.price_step, params.price_rounding_precision)

        new_sell_price = round(mid_price * (1 + params.positive_quote_distance_bps / 10000), params.price_rounding_precision)
        if new_sell_price <= best_ask:
            new_sell_price = round(best_ask + params.price_step, params.price_rounding_precision)

        if params.enable_long_quotes:
            new_buy_size = params.long_reduction_func()
        if params.enable_short_quotes:
            new_sell_size = params.short_reduction_func()

        current_quote = self.current_quotes[contract]

        buy_price_diff = abs(new_buy_price - current_quote['buy_price']) / current_quote['buy_price'] if current_quote['buy_price'] != 0 else float('inf')
        sell_price_diff = abs(new_sell_price - current_quote['sell_price']) / current_quote['sell_price'] if current_quote['sell_price'] != 0 else float('inf')

        should_update_buy = buy_price_diff >= params.long_adjustment_threshold_bps / 10000
        should_update_sell = sell_price_diff >= params.short_adjustment_threshold_bps / 10000

        if should_update_buy or should_update_sell or current_quote['buy_price'] == 0:

            if should_update_buy and params.enable_long_quotes:
                current_quote['buy_price'] = new_buy_price
                current_quote['buy_size'] = new_buy_size
            if should_update_sell and params.enable_short_quotes:
                current_quote['sell_price'] = new_sell_price
                current_quote['sell_size'] = new_sell_size

            asyncio.create_task(self.quote_update_queue.put(contract))






    
    async def wait_for_quote_update(self):
        return await self.quote_update_queue.get()
    
    async def run(self):
        await asyncio.gather(
            self.orderbook_manager.run(),
            self.inventory_manager.run()
        )

    async def cleanup(self):
        await self.orderbook_manager.cleanup()
        # Add cleanup for inventory manager if needed

# Example usage
async def main():
    contracts = ["ETH_USDT"]
    quote_generator = QuoteGenerator(contracts)

    # Set parameters for each contract
    for contract in contracts:
        params = quote_generator.contract_params[contract]
        params.set_quote_distances(10, 10)
        params.set_adjustment_thresholds(5, 5)
        params.set_price_rounding_precision(8) # rounds prices being submitted
        params.set_enable_quotes(True, True) #enables quoting both bids and asks
        params.set_price_step(0)

    # Example of setting different parameters for ETH_USDT
    eth_params = quote_generator.contract_params["ETH_USDT"]
    eth_params.set_enable_quotes(True, True)  # Quote both sides for ETH

    try:
        await quote_generator.run()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await quote_generator.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



"""
strategy class:
streams orders for a specific contract for the embedded strategy
methods:

1. Stream orderbook
2. Function that calls on an orderbook update
3. Import and load features
4. Whenever orderbook update happens, #2 is called 
5. #2 calls #3 to get features and returns price after features are applied
6. This price is then used to update quotes for each contract
7. 


"""
import asyncio
from typing import List, Dict, Callable
from orderbook_gateio import OrderbookGateio
from contract_manager import ContractParams
from features_gateio import Features
import numpy as np

class QuoteGenerator:
    def __init__(self, contracts: List[str], orderbook_size: int = 20):
        self.contracts = contracts
        self.orderbook_manager = OrderbookGateio(contracts, orderbook_size)
        self.contract_params: Dict[str, ContractParams] = {}
        
        for contract in contracts:
            self.contract_params[contract] = ContractParams(
                contract=contract,
                max_long=1.0,
                max_short=-1.0,
                default_long_size=0.1,
                default_short_size=0.1
            )

        self.quote_callback: Callable[[str, Dict], None] = None
        self.is_running = False

    def set_quote_callback(self, callback: Callable[[str, Dict], None]):
        self.quote_callback = callback

    def update_contract_position(self, contract: str, new_position: float):
        if contract in self.contract_params:
            self.contract_params[contract].update_position(new_position)

    def set_quote_distances(self, contract: str, positive_bps: float, negative_bps: float):
        if contract in self.contract_params:
            self.contract_params[contract].set_quote_distances(positive_bps, negative_bps)

    async def start(self):
        if self.is_running:
            print("QuoteGenerator is already running.")
            return

        self.is_running = True
        self.orderbook_manager.on_update_callback = self.on_orderbook_update
        await self.orderbook_manager.initialize_orderbooks()
        await self.orderbook_manager.run()

    def on_orderbook_update(self, contract: str, bids: np.ndarray, asks: np.ndarray):
        quotes = self.generate_quotes(contract, bids, asks)
        if self.quote_callback:
            self.quote_callback(contract, quotes)

    def generate_quotes(self, contract: str, bids: np.ndarray, asks: np.ndarray) -> Dict:
        features = Features(bids, asks)
        vwmp = features.volume_weighted_mid_price(depth=10)
        params = self.contract_params[contract]

        positive_distance = vwmp * (params.positive_quote_distance_bps / 10000)
        negative_distance = vwmp * (params.negative_quote_distance_bps / 10000)

        buy_price = vwmp - negative_distance
        sell_price = vwmp + positive_distance

        buy_size = self.calculate_buy_size(params)
        sell_size = self.calculate_sell_size(params)

        return {
            "buy": {"price": buy_price, "size": buy_size},
            "sell": {"price": sell_price, "size": sell_size},
            "vwmp": vwmp
        }

    def calculate_buy_size(self, params: ContractParams) -> float:
        if 0 <= params.current_position <= params.max_long:
            return max(0, params.default_long_size - (params.current_position * 0.1))
        return params.default_long_size

    def calculate_sell_size(self, params: ContractParams) -> float:
        if params.max_short <= params.current_position <= 0:
            return max(0, abs(params.default_short_size) - (abs(params.current_position) * 0.1))
        return abs(params.default_short_size)

    async def cleanup(self):
        self.is_running = False
        await self.orderbook_manager.cleanup()

# Example usage
async def main():
    contracts = ["BTC_USDT"]
    quote_generator = QuoteGenerator(contracts)

    def print_quotes(contract: str, quotes: Dict):
        print(f"Quotes for {contract}:")
        print(f"  Buy: Price = {quotes['buy']['price']:.2f}, Size = {quotes['buy']['size']:.4f}")
        print(f"  Sell: Price = {quotes['sell']['price']:.2f}, Size = {quotes['sell']['size']:.4f}")
        print(f"  VWMP: {quotes['vwmp']:.2f}")

    quote_generator.set_quote_callback(print_quotes)

    # Set up contract parameters
    for contract in contracts:
        quote_generator.set_quote_distances(contract, positive_bps=10, negative_bps=10)
        quote_generator.update_contract_position(contract, 0)  # Start with no position

    try:
        await quote_generator.start()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await quote_generator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
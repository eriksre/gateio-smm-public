import asyncio
from typing import Dict, List
import numpy as np
from orderbook_gateio import OrderbookGateio
from inventory_manager_gateio import InventoryManagerGateio
from features_gateio import Features

class QuoteGenerator:
    def __init__(self, contracts: List[str], orderbook_size: int = 20):
        self.contracts = contracts
        self.orderbook_manager = OrderbookGateio(contracts=contracts, size=orderbook_size)
        self.orderbook_manager.on_update_callback = self.on_orderbook_update
        self.inventory_manager = InventoryManagerGateio()
        self.positions: Dict[str, float] = {contract: 0.0 for contract in contracts}
        self.features: Dict[str, Features] = {}

    async def start(self):
        orderbook_task = asyncio.create_task(self.orderbook_manager.run())
        inventory_task = asyncio.create_task(self.inventory_manager.run())
        await asyncio.gather(orderbook_task, inventory_task)

    def on_orderbook_update(self, contract: str, bids: np.ndarray, asks: np.ndarray):
        self.features[contract] = Features(bids, asks)
        vwap = self.features[contract].volume_weighted_mid_price(depth=10)  # Using depth of 10, adjust as needed
        print(f"Received orderbook update for {contract}")
        print(f"Volume-weighted average price: {vwap}")
        print(f"Current position: {self.positions[contract]}")
        # Implement your quoting logic here, considering VWAP and position

    async def update_positions(self):
        while True:
            for contract in self.contracts:
                currency = contract.split('_')[0]  # Assuming format like 'BTC_USDT'
                position = self.inventory_manager.get_balance(currency)
                if self.positions[contract] != position:
                    self.positions[contract] = position
                    print(f"Position updated for {contract}: {position}")
            await asyncio.sleep(1)  # Update every second

    async def run(self):
        try:
            start_task = asyncio.create_task(self.start())
            position_update_task = asyncio.create_task(self.update_positions())
            await asyncio.gather(start_task, position_update_task)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await self.orderbook_manager.cleanup()
            if hasattr(self.inventory_manager, 'cleanup'):
                await self.inventory_manager.cleanup()

async def main():
    contracts = ["BTC_USDT"]
    quote_generator = QuoteGenerator(contracts)
    await quote_generator.run()

if __name__ == "__main__":
    asyncio.run(main())
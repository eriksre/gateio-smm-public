import asyncio
from typing import List, Tuple, Callable
from get_gateio import GetGateio
from ws_gateio import WSGateio

class InventoryManagerGateio:
    def __init__(self):
        self.get_gateio = GetGateio()
        self.ws_gateio = WSGateio()
        self.positions: List[Tuple[str, float]] = []
        self.on_position_update: Callable[[List[Tuple[str, float]]], None] = None

    async def initialize_positions(self):
        async with self.get_gateio as gateio:
            self.positions = await gateio.get_positions()
        if self.on_position_update:
            self.on_position_update(self.positions)

    def update_position(self, contract: str, size_change: float):
        for i, (pos_contract, size) in enumerate(self.positions):
            if pos_contract == contract:
                new_size = float(size) + size_change
                self.positions[i] = (contract, new_size)
                if self.on_position_update:
                    self.on_position_update(self.positions)
                return
        # If the contract is not in the positions list, add it
        self.positions.append((contract, size_change))
        if self.on_position_update:
            self.on_position_update(self.positions)

    def get_position(self, contract: str) -> float:
        for pos_contract, size in self.positions:
            if pos_contract == contract:
                return float(size)
        return 0.0

    async def handle_user_trade(self, message):
        if message.get("event") == "update":
            for trade in message.get("result", []):
                contract = trade.get("contract")
                size_change = float(trade.get("size", 0))
                self.update_position(contract, size_change)

    async def run(self):
        await self.initialize_positions()
        self.ws_gateio.message_callback = self.handle_user_trade
        await self.ws_gateio.subscribe_user_trades()




def print_positions(positions):
    print("Current positions:")
    for contract, size in positions:
        print(f"  {contract}: {size}")
    print("------------------------")

async def main():
    inventory_manager = InventoryManagerGateio()
    inventory_manager.on_position_update = print_positions

    print("Starting inventory manager...")
    await inventory_manager.run()

if __name__ == "__main__":
    asyncio.run(main())
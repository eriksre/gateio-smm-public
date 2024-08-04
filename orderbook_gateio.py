import asyncio
import numpy as np
from typing import Dict, Any, List, Callable
from baseorderbook import Orderbook
from ws_gateio import WSGateio
from get_gateio import GetGateio

class OrderbookGateio:
    def __init__(self, contracts: List[str], size: int) -> None:
        self.ws_gateio = WSGateio()
        self.get_gateio = GetGateio()
        self.contracts = contracts
        self.size = size
        self.orderbooks: Dict[str, Orderbook] = {contract: Orderbook(size) for contract in contracts}
        self.base_ids: Dict[str, int] = {contract: None for contract in contracts}
        self.cached_updates: Dict[str, List[Dict[str, Any]]] = {contract: [] for contract in contracts}
        self.is_initialized: Dict[str, bool] = {contract: False for contract in contracts}
        self.running = False
        self.on_update_callback = None

    async def initialize_orderbooks(self) -> None:
        self.ws_gateio.message_callback = self.process_ws_message
        for contract in self.contracts:
            self.ws_gateio.add_orderbook_subscription(contract)
        
        ws_task = asyncio.create_task(self.ws_gateio.start_subscriptions())

        await asyncio.sleep(2)

        async with self.get_gateio as gateio:
            for contract in self.contracts:
                initial_data = await gateio.get_orderbook(contract, self.size)
                self.process_ob_snapshot(contract, initial_data)

        for contract in self.contracts:
            self.is_initialized[contract] = True
            print(f"Orderbook for {contract} initialized successfully")
            await self.apply_updates(contract)

    def process_ws_message(self, data: Dict[str, Any]) -> None:
        if 'result' in data and isinstance(data['result'], dict):
            update = data['result']
            contract = update.get('s')
            if contract in self.contracts and ('a' in update or 'b' in update):
                if self.is_initialized[contract]:
                    asyncio.create_task(self.apply_single_update(contract, update))
                else:
                    self.cached_updates[contract].append(update)

    def process_ob_snapshot(self, contract: str, data: Dict[str, Any]) -> None:
        if isinstance(data, dict) and 'asks' in data and 'bids' in data:
            ob = self.orderbooks[contract]
            ob.asks = np.array([[float(ask['p']), float(ask['s'])] for ask in data['asks']])
            ob.bids = np.array([[float(bid['p']), float(bid['s'])] for bid in data['bids']])
            self.base_ids[contract] = self.extract_obid(data)
            if self.on_update_callback:
                self.on_update_callback(contract, ob.bids, ob.asks)
        else:
            raise ValueError(f"Unexpected orderbook snapshot data structure for {contract}")

    async def apply_updates(self, contract: str) -> None:
        for update in self.cached_updates[contract]:
            await self.apply_single_update(contract, update)
        self.cached_updates[contract].clear()

    async def apply_single_update(self, contract: str, update: Dict[str, Any]) -> None:
        try:
            U, u = self.extract_identifier(update)
        except KeyError:
            return

        if self.base_ids[contract] is None or u < self.base_ids[contract] + 1:
            return

        ob = self.orderbooks[contract]
        if U <= self.base_ids[contract] + 1 <= u:
            if 'a' in update:
                asks = np.array([[float(ask['p']), float(ask['s'])] for ask in update['a']])
                ob.update_asks(asks)

            if 'b' in update:
                bids = np.array([[float(bid['p']), float(bid['s'])] for bid in update['b']])
                ob.update_bids(bids)

            self.base_ids[contract] = u
            if self.on_update_callback:
                self.on_update_callback(contract, ob.bids, ob.asks)
        elif U > self.base_ids[contract] + 1:
            await self.reconstruct_orderbook(contract)

    @staticmethod
    def extract_identifier(data: Dict[str, Any]) -> tuple[int, int]:
        if 'U' in data and 'u' in data:
            return int(data['U']), int(data['u'])
        raise KeyError("Update does not contain 'U' and 'u' fields")

    @staticmethod
    def extract_obid(data: Dict[str, Any]) -> int:
        return int(data.get('id', 0))

    async def reconstruct_orderbook(self, contract: str) -> None:
        self.cached_updates[contract].clear()
        self.is_initialized[contract] = False
        async with self.get_gateio as gateio:
            initial_data = await gateio.get_orderbook(contract, self.size)
        self.process_ob_snapshot(contract, initial_data)
        self.is_initialized[contract] = True
        await self.apply_updates(contract)

    async def run(self) -> None:
        self.running = True
        await self.initialize_orderbooks()
        while self.running:
            await asyncio.sleep(1)

    async def cleanup(self) -> None:
        print("Cleaning up OrderbookGateio...")
        self.running = False
        if hasattr(self.ws_gateio, 'cleanup'):
            await self.ws_gateio.cleanup()
        print("OrderbookGateio cleanup completed")

def print_orderbook(contract: str, bids: np.ndarray, asks: np.ndarray):
    print(f"\nOrderbook Update for {contract}:")
    print("Bids:")
    for bid in bids[:5]:  # Print top 5 bids
        print(f"Price: {bid[0]}, Size: {bid[1]}")
    print("Asks:")
    for ask in asks[:5]:  # Print top 5 asks
        print(f"Price: {ask[0]}, Size: {ask[1]}")
    print("-" * 40)

async def main():
    contracts = ["BTC_USDT"]
    orderbook_manager = OrderbookGateio(contracts=contracts, size=20)
    orderbook_manager.on_update_callback = print_orderbook

    try:
        await orderbook_manager.run()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await orderbook_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
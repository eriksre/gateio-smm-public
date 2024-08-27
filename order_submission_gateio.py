import asyncio
from typing import List, Dict, Optional, Tuple
from post_gateio import PostGateio
from oms_gateio import OrderManagerGateio, Order
from datetime import datetime
# from order_logger import OrderLogger 


"""
class combines post, order manager, and order logger so that positions and orders can be kept track of
"""


class OrderSubmissionGateio:
    def __init__(self):
        self.post_gateio = PostGateio()
        self.order_manager = OrderManagerGateio()
        self.session = None

    async def __aenter__(self):
        self.session = await self.post_gateio.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.post_gateio.__aexit__(exc_type, exc, tb)

    def _process_created_orders(self, created_orders: List[Dict]) -> List[Dict]:
        """
        Returns a list of dictionaries containing orders with strategy tags.
        """
        processed_orders = []
        for order in created_orders:
            processed_order = {
                'order_id': str(order['id']),
                'contract': order['contract'],
                'price': order['price'],
                'size': order['size'],
                'side': order['side'],
                'status': order['status'],
                'strategy': order.get('strategy', '')  # Get strategy directly from the order
            }
        return processed_orders

    def _extract_strategy(self, order: Dict) -> Tuple[Dict, str]:
        strategy = order.pop('strategy', '')
        return order, strategy


    """
    re-do the logic on this wait for confirmation method
    essentially, in the internal oms, don't have a delay or wait for confirmation, but as soon as the 
    order has been inserted into the oms, then can run operations like cancel and whatnot. until then, this function has not finished executing
    thought - does this mean this needs to not be an async method?
    ############################################
    
    """
    async def _wait_for_orders_confirmation(self, orders: List[Dict]):
        """
        waits for orders to be 
        """
        while True:
            all_confirmed = True
            for order in orders:
                if order['order_id'] not in self.order_manager.live_orders:
                    all_confirmed = False
                    break
            
            if all_confirmed:
                return
            
            # await asyncio.sleep(0) yields control back to the event loop,
            # allowing other coroutines to run. It's essentially a way to
            # cooperatively multitask without blocking the entire program.
            # This prevents the while loop from hogging all the CPU time.
            await asyncio.sleep(0)



    async def submit_bulk_orders(self, orders_data: List[Dict]) -> List[Order]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        try:
            exchange_orders, strategies = zip(*[self._extract_strategy(order) for order in orders_data])
            
            created_orders = await self.post_gateio.create_order_batch(exchange_orders)


            # add strategy param to given order in order manager logic
            for created_order, strategy in zip(created_orders, strategies):
                created_order['strategy'] = strategy
            
            processed_orders = self._process_created_orders(created_orders)
            self.order_manager.add_orders(processed_orders)

            #await self._wait_for_orders_confirmation(processed_orders)
            print(f"Processed orders: {processed_orders}")

            return processed_orders
        
        except Exception as e:
            print(f"Error submitting bulk orders: {e}")
            print(f"Orders data: {orders_data}")
            print(f"Exchange orders: {exchange_orders}")
            return []



    async def cancel_orders_by_id(self, order_ids: List[str]) -> List[Dict]:
        """
        cancel by order id
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        try:
            cancelled_orders = await self.post_gateio.cancel_order_batch(order_ids)
            self.order_manager.remove_orders(order_ids)
            self.order_manager.update_order_status(order_ids, "cancelled")
            
            # Log cancelled orders
            # for order in cancelled_orders:
            #     self.order_logger.log_order({**order, 'status': 'cancelled'})
            
            return cancelled_orders
        except Exception as e:
            print(f"Error cancelling bulk orders: {e}")
            return []


    async def cancel_orders_by_strategy_or_symbol(self, strategy: Optional[str] = None, symbol: Optional[str] = None) -> List[Dict]:
        """
        Cancel orders by strategy, symbol, or both. At least one of strategy or symbol must be provided.

        :param strategy: Optional strategy name to cancel orders for
        :param symbol: Optional symbol (contract) to cancel orders for
        :return: List of cancelled orders
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        if strategy is None and symbol is None:
            raise ValueError("At least one of strategy or symbol must be provided")

        try:
            # Get live orders filtered by strategy and/or symbol
            live_orders = self.order_manager.get_live_orders(strategy=strategy, contract=symbol)
            
            if not live_orders:
                return []

            order_ids = [order['order_id'] for order in live_orders]
            
            # Cancel the filtered orders
            cancelled_orders = await self.post_gateio.cancel_order_batch(order_ids)
            self.order_manager.update_order_status(order_ids, "cancelled")
            
            # Remove cancelled orders from the order manager
            self.order_manager.remove_orders(order_ids)
            
            # Log cancelled orders
            # for order in cancelled_orders:
            #     self.order_logger.log_order({**order, 'status': 'cancelled'})
            
            return cancelled_orders
        except Exception as e:
            print(f"Error cancelling orders by strategy or symbol: {e}")
            return []

    def get_live_orders(self, strategy: Optional[str] = None, contract: Optional[str] = None) -> List[Dict]:
        """
        Get live orders filtered by strategy, contract, or both.
        
        :param strategy: Optional strategy name to filter orders
        :param contract: Optional contract symbol to filter orders
        :return: List of live orders matching the specified criteria
        """
        return self.order_manager.get_live_orders(strategy=strategy, contract=contract)


if __name__ == "__main__":

    async def main():
        async with OrderSubmissionGateio() as order_submission:
            # Create orders in bulk
            orders_data = [
                {
                    "contract": "BTC_USDT",
                    "size": 1,
                    "price": 50000,
                    "side": "buy",
                    "text": "strategy_1"
                },
                {
                    "contract": "ETH_USDT",
                    "size": 1,
                    "price": 2000,
                    "side": "buy",
                    "text": "t-strategy_2"
                }
            ]

            created_orders = await order_submission.submit_bulk_orders(orders_data)
            print("Created orders:", created_orders)


            await asyncio.sleep(5)
            # Cancel order by strategy
            cancelled_by_strategy = await order_submission.cancel_orders_by_strategy_or_symbol(strategy="strategy_1")
            print("Cancelled orders by strategy:", cancelled_by_strategy)

            # # Cancel order by symbol
            # cancelled_by_symbol = await order_submission.cancel_orders_by_strategy_or_symbol(symbol="ETH_USDT")
            # print("Cancelled orders by symbol:", cancelled_by_symbol)

            # # Check if any orders were actually cancelled
            # if not cancelled_by_strategy and not cancelled_by_symbol:
            #     print("Warning: No orders were cancelled. Check if the orders were created successfully.")

    asyncio.run(main())


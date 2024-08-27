import asyncio
from typing import List, Dict, Optional, Tuple
from post_gateio import PostGateio
from oms_gateio import OrderManagerGateio



from post_gateio import PostGateio
import asyncio


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

    async def submit_bulk_orders(self, orders_data: List[Dict]) -> List[Dict]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        try:
            # Create pending orders in the order manager
            internal_ids = self.order_manager.create_orders_from_list(orders_data)

            # Submit orders to the exchange
            exchange_submission = await self.post_gateio.create_order_batch(orders_data)

            # Process the exchange response and update order manager
            submitted_orders = []
            for internal_id, exchange_order in zip(internal_ids, exchange_submission):
                if exchange_order.get('status') == 'open':
                    self.order_manager.update_order_with_exchange_details(internal_id, exchange_order)
                    submitted_order = self.order_manager.get_order(str(exchange_order['id']))
                    if submitted_order:
                        submitted_orders.append(submitted_order)
                else:
                    # Handle failed orders if necessary
                    print(f"Order submission failed for internal ID: {internal_id}")

            return submitted_orders

        except Exception as e:
            print(f"Error submitting bulk orders: {str(e)}")
            return []
        





    async def cancel_bulk_orders(self, order_ids: List[str]) -> List[Dict]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        try:
            # Cancel orders on the exchange
            cancellation_results = await self.post_gateio.cancel_order_batch(order_ids)
            for order in cancellation_results:
                if order['succeeded'] == 'False':
                    retry_count = 0
                    max_retries = 3
                    while retry_count < max_retries:
                        try:
                            print(f"Retrying cancellation for order ID: {order['order_id']}. Attempt {retry_count + 1}")
                            # Attempt to cancel the order again
                            retry_result = await self.post_gateio.cancel_order(order['order_id'])
                            if retry_result['succeeded'] == 'True':
                                print(f"Retry successful for order ID: {order['order_id']}")
                                break
                        except Exception as retry_error:
                            print(f"Retry failed for order ID: {order['order_id']}. Error: {str(retry_error)}")
                        retry_count += 1
                    
                    # will cause issues if an order is already filled???
                    # if retry_count == max_retries:
                    #     raise RuntimeError(f"Order cancellation failed after {max_retries} attempts for order ID: {order['order_id']}")

            # Update order manager
            self.order_manager.cancel_orders(order_ids)
            return cancellation_results

        except Exception as e:
            print(f"Error cancelling bulk orders: {str(e)}")
            return []


    async def cancel_orders_by_strategy(self, strategy: str) -> List[Dict]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        try:
            # Get live orders filtered by strategy
            live_orders = self.order_manager.get_live_orders(text=strategy)
            
            if not live_orders:
                print(f"No live orders found for strategy: {strategy}")
                return []

            order_ids = [order['order_id'] for order in live_orders]
            
            # Cancel the filtered orders
            cancelled_orders = await self.cancel_bulk_orders(order_ids)
            return cancelled_orders

        except Exception as e:
            print(f"Error cancelling orders by strategy: {str(e)}")
            return []



    async def cancel_orders_by_contract(self, contract: str) -> List[Dict]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' to create OrderSubmissionGateio instance.")
        
        try:
            # Get live orders filtered by contract
            live_orders = self.order_manager.get_live_orders(contract=contract)
            
            if not live_orders:
                print(f"No live orders found for contract: {contract}")
                return []

            order_ids = [order['order_id'] for order in live_orders]
            
            # Cancel the filtered orders
            cancelled_orders = await self.cancel_bulk_orders(order_ids)
            return cancelled_orders

        except Exception as e:
            print(f"Error cancelling orders by contract: {str(e)}")
            return []


    def get_live_orders(self, text: str = None, contract: str = None) -> List[Dict]:
        return self.order_manager.get_live_orders(text, contract)

    def get_order(self, order_id: str) -> Dict:
        return self.order_manager.get_order(order_id)  

    


    

# Example usage
async def main():
    async with OrderSubmissionGateio() as order_submission:
        orders_to_submit = [
            {
                "contract": "BTC_USDT",
                "size": "1",
                "price": "50000",
                "side": "buy",
                "text": "t-example-1"
            },
            {
                "contract": "ETH_USDT",
                "size": "1",
                "price": "2000",
                "side": "buy",
                "text": "t-example-2"
            }
        ]

        import time
        time1 = time.time()


        submitted_orders = await order_submission.submit_bulk_orders(orders_to_submit)
        print("Submitted orders:", submitted_orders)

        cancelled_orders1 = await order_submission.cancel_orders_by_strategy("t-example-1")
        cancelled_orders2 = await order_submission.cancel_orders_by_contract("ETH_USDT")

        time2 = time.time()
        print(f"time: {time2-time1}")



if __name__ == "__main__":
    asyncio.run(main())



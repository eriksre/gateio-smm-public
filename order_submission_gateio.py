import asyncio
from typing import List, Dict
from post_gateio import PostGateio
from oms_gateio import OrderManagerGateio, Order
from datetime import datetime

class OrderSubmissionGateio:
    def __init__(self, post_gateio: PostGateio, order_manager: OrderManagerGateio):
        self.post_gateio = post_gateio
        self.order_manager = order_manager

    async def submit_bulk_orders(self, orders_data: List[Dict]) -> List[Order]:
        try:
            created_orders = await self.post_gateio.create_order_batch(orders_data)
            processed_orders = self._process_created_orders(created_orders)
            self.order_manager.add_orders(processed_orders)
            return processed_orders
        except Exception as e:
            print(f"Error submitting bulk orders: {e}")
            return []

    def _process_created_orders(self, created_orders: List[Dict]) -> List[Dict]:
        processed_orders = []
        for order in created_orders:
            processed_order = {
                'order_id': str(order['id']),
                'contract': order['contract'],
                'price': order['price'],
                'size': order['size'],
                'side': 'buy' if float(order['size']) > 0 else 'sell',
                'status': order['status']
            }
            processed_orders.append(processed_order)
        return processed_orders

    async def cancel_bulk_orders(self, order_ids: List[str]) -> List[Dict]:
        try:
            cancelled_orders = await self.post_gateio.cancel_order_batch(order_ids)
            self.order_manager.remove_orders(order_ids)
            return cancelled_orders
        except Exception as e:
            print(f"Error cancelling bulk orders: {e}")
            return []

    def get_live_orders(self, contract: str = None) -> List[Order]:
        if contract:
            return self.order_manager.get_live_orders_by_contract(contract)
        else:
            return list(self.order_manager.get_live_orders().values())

async def main():
    async with PostGateio() as post_gateio:
        order_manager = OrderManagerGateio()
        order_submission = OrderSubmissionGateio(post_gateio, order_manager)

        # Submit two orders
        orders_data = [
            {"contract": "BTC_USDT", "size": 1, "price": "55000", "side": "buy"},
            {"contract": "ETH_USDT", "size": 1, "price": "2300", "side": "buy"}
        ]
        
        created_orders = await order_submission.submit_bulk_orders(orders_data)
        print("Created orders:")
        for order in created_orders:
            print(order)

        live_orders = order_submission.get_live_orders()
        print("\nLive orders after creation:")
        for order in live_orders:
            print(order)

        # Cancel the orders we just created
        order_ids_to_cancel = [order['order_id'] for order in created_orders]
        cancelled_orders = await order_submission.cancel_bulk_orders(order_ids_to_cancel)
        print("\nCancelled orders:")
        for order in cancelled_orders:
            print(order)

        live_orders_after_cancellation = order_submission.get_live_orders()
        print("\nLive orders after cancellation:")
        for order in live_orders_after_cancellation:
            print(order)

if __name__ == "__main__":
    asyncio.run(main())

    
{'refu': 0, 'tkfr': '0.00048', 'mkfr': '0.0002', 'contract': 'BTC_USDT', 'id': 511513575493, 'price': '55000', 'tif': 'gtc', 'iceberg': 0, 'text': 'api', 'user': 14678126, 'is_reduce_only': False, 'is_close': False, 'is_liq': False, 'fill_price': '0', 'create_time': 1722759655.884, 'update_time': 1722759655.884, 'status': 'open', 'left': 1, 'refr': '0', 'size': 1, 'biz_info': '-', 'amend_text': '-', 'stp_act': '-', 'stp_id': 0, 'succeeded': True, 'update_id': 1, 'pnl': '0', 'pnl_margin': '0'}
{'refu': 0, 'tkfr': '0.00048', 'mkfr': '0.0002', 'contract': 'ETH_USDT', 'id': 511513575494, 'price': '2300', 'tif': 'gtc', 'iceberg': 0, 'text': 'api', 'user': 14678126, 'is_reduce_only': False, 'is_close': False, 'is_liq': False, 'fill_price': '0', 'create_time': 1722759655.884, 'update_time': 1722759655.884, 'status': 'open', 'left': 1, 'refr': '0', 'size': 1, 'biz_info': '-', 'amend_text': '-', 'stp_act': '-', 'stp_id': 0, 'succeeded': True, 'update_id': 1, 'pnl': '0', 'pnl_margin': '0'}
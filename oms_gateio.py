from typing import Dict, List, Optional
from datetime import datetime
import uuid

class OrderManagerGateio:
    def __init__(self):
        self.pending_orders: Dict[str, Dict] = {}
        self.live_orders: Dict[str, Dict] = {}
        self.cancelled_orders: Dict[str, Dict] = {}
        self.filled_orders: Dict[str, Dict] = {}


    def create_order(self, order_data: Dict) -> str:
        internal_id = str(uuid.uuid4())
        order = {
            'order_id': None,
            'internal_id': internal_id,
            'internal_creation_time': float(datetime.now().timestamp()),
            'internal_status': 'pending',
            'contract': order_data['contract'],
            'price': float(order_data['price']),
            'quantity': float(order_data['size']),
            'side': order_data['side'],
            'text': order_data['text'],
            'exchange_creation_time': None,
            'refu': None,
            'status': None
        }
        self.pending_orders[internal_id] = order
        return internal_id

    def create_orders_from_list(self, orders_data: List[Dict]) -> List[str]:
        return [self.create_order(order_data) for order_data in orders_data]

    def update_order_with_exchange_details(self, internal_id: str, exchange_order: Dict):
        if internal_id in self.pending_orders:
            order = self.pending_orders.pop(internal_id)
            order['order_id'] = str(exchange_order['id'])
            order['exchange_creation_time'] = exchange_order['create_time']
            order['refu'] = bool(exchange_order['refu'])
            order['status'] = exchange_order['status']
            order['internal_status'] = 'live'
            self.live_orders[order['order_id']] = order

    def update_order_after_lifecycle(self, internal_id: str):
        if internal_id in self.live_orders:
            order = self.live_orders.pop(internal_id)


    def get_live_orders(self, text: Optional[str] = None, contract: Optional[str] = None) -> List[Dict]:
        filtered_orders = self.live_orders.values()
        
        if text:
            filtered_orders = [order for order in filtered_orders if order['text'] == text]
        
        if contract:
            filtered_orders = [order for order in filtered_orders if order['contract'] == contract]
        
        return list(filtered_orders)

    def get_order(self, order_id: str) -> Optional[Dict]:
        return self.live_orders.get(order_id)
    

    def cancel_orders(self, order_ids: List[str]):
        for order_id in order_ids:
            if order_id in self.live_orders:
                order = self.live_orders.pop(order_id)
                order['internal_status'] = 'cancelled'
                order['status'] = 'cancelled'
                #self.cancelled_orders[order_id] = order
                print("uncomment line 71 oms_gateio.py file when running this properly. this to keep ram usage low, otherwise cancelled orders pile in memory")
            else:
                print(f"Order ID {order_id} not found in live orders.")







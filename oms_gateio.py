from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Order:
    order_id: str
    contract: str
    price: float
    quantity: float
    side: str
    creation_time: datetime
    status: str = "open"

class OrderManagerGateio:
    def __init__(self):
        self.live_orders: Dict[str, Order] = {}

    def add_orders(self, orders: List[Dict]) -> None:
        """
        Add new orders to the live orders dictionary.
        
        :param orders: List of order dictionaries returned from the exchange
        """
        for order_dict in orders:
            order_id = order_dict['order_id']
            self.live_orders[order_id] = Order(
                order_id=order_id,
                contract=order_dict['contract'],
                price=float(order_dict['price']),
                quantity=float(order_dict['size']),
                side=order_dict['side'],
                creation_time=datetime.now(),
                status=order_dict['status']
            )
        # print("Orders added to OrderManager:")
        # for order in self.live_orders.values():
        #     print(order)

    def remove_orders(self, order_ids: List[str]) -> None:
        """
        Remove orders from the live orders dictionary.
        
        :param order_ids: List of order IDs to remove
        """
        for order_id in order_ids:
            self.live_orders.pop(order_id, None)

    def update_order_status(self, order_id: str, new_status: str) -> None:
        if order_id in self.live_orders:
            self.live_orders[order_id].status = new_status

    def get_live_orders(self) -> Dict[str, Dict]:
        """
        Get all live orders as dictionaries.
        
        :return: Dictionary of live orders
        """
        return {order_id: self._order_to_dict(order) for order_id, order in self.live_orders.items()}

    def get_live_orders_by_contract(self, contract: str) -> List[Dict]:
        """
        Get live orders for a specific contract as dictionaries.
        
        :param contract: Contract symbol
        :return: List of live orders for the specified contract
        """
        return [self._order_to_dict(order) for order in self.live_orders.values() if order.contract == contract]

    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Get a specific order by its ID as a dictionary.
        
        :param order_id: ID of the order to retrieve
        :return: Order dictionary if found, None otherwise
        """
        order = self.live_orders.get(order_id)
        return self._order_to_dict(order) if order else None

    @staticmethod
    def _order_to_dict(order: Order) -> Dict:
        """
        Convert an Order object to a dictionary.
        """
        return {
            'order_id': order.order_id,
            'contract': order.contract,
            'price': order.price,
            'size': order.quantity,
            'side': order.side,
            'creation_time': order.creation_time.isoformat(),
            'status': order.status
        }
# Example usage:
# order_manager = OrderManagerGateio()
# 
# # Add new orders
# new_orders = [
#     {'order_id': '1', 'contract': 'BTC_USDT', 'price': '50000', 'size': '0.1', 'side': 'buy'},
#     {'order_id': '2', 'contract': 'ETH_USDT', 'price': '3000', 'size': '1', 'side': 'sell'}
# ]
# order_manager.add_orders(new_orders)
# 
# # Get live orders
# live_orders = order_manager.get_live_orders()
# print(live_orders)
# 
# # Update order status
# order_manager.update_order_status('1', 'filled')
# 
# # Remove an order
# order_manager.remove_orders(['2'])
# 
# # Get orders for a specific contract
# btc_orders = order_manager.get_live_orders_by_contract('BTC_USDT')
# print(btc_orders)
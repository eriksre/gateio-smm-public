import csv
import os
from datetime import datetime

class OrderLogger:
    def __init__(self):
        self.desktop_path = os.path.expanduser("~/Desktop")
        self.csv_file_path = os.path.join(self.desktop_path, "order_log.csv")
        self._create_csv_if_not_exists()

    def _create_csv_if_not_exists(self):
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'order_id', 'contract', 'price', 'size', 'side', 'status', 'strategy']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

    def log_order(self, order):
        with open(self.csv_file_path, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'order_id', 'contract', 'price', 'size', 'side', 'status', 'strategy']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            order_data = {
                'timestamp': datetime.now().isoformat(),
                'order_id': order['order_id'],
                'contract': order['contract'],
                'price': order['price'],
                'size': order['size'],
                'side': order['side'],
                'status': order['status'],
                'strategy': order['strategy']
            }
            writer.writerow(order_data)

    def log_orders(self, orders):
        for order in orders:
            self.log_order(order)
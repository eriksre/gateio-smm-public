import numpy as np
from typing import Dict

class Features:
    def __init__(self, bids: np.ndarray, asks: np.ndarray):
        self.bids = bids
        self.asks = asks

    def volume_weighted_mid_price(self, depth: int) -> float:
        """
        Calculate the volume-weighted mid-price (VWMP) at a given depth.
        
        :param depth: The number of levels to consider in the orderbook.
        :return: The volume-weighted mid-price.
        """
        bids = self.bids[:depth]
        asks = self.asks[:depth]
        
        total_bid_volume = np.sum(bids[:, 1])
        total_ask_volume = np.sum(asks[:, 1])
        
        weighted_bid_price = np.sum(bids[:, 0] * bids[:, 1]) / total_bid_volume if total_bid_volume > 0 else 0
        weighted_ask_price = np.sum(asks[:, 0] * asks[:, 1]) / total_ask_volume if total_ask_volume > 0 else 0
        
        if weighted_bid_price == 0 or weighted_ask_price == 0:
            return np.NaN
        
        return (weighted_bid_price + weighted_ask_price) / 2

    def best_bid_ask(self) -> Dict[str, float]:
        """
        Get the best bid and ask prices.
        
        :return: A dictionary with 'bid' and 'ask' keys.
        """
        return {
            'bid': self.bids[0, 0] if len(self.bids) > 0 else 0,
            'ask': self.asks[0, 0] if len(self.asks) > 0 else 0
        }

    def order_book_imbalance(self, depth: int) -> float:
        """
        Calculate the order book imbalance at a given depth.
        
        :param depth: The number of levels to consider in the orderbook.
        :return: The order book imbalance (-1 to 1, where positive values indicate more bid volume).
        """
        bid_volume = np.sum(self.bids[:depth, 1])
        ask_volume = np.sum(self.asks[:depth, 1])
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return 0
        
        return (bid_volume - ask_volume) / total_volume

    # You can add more features here as needed
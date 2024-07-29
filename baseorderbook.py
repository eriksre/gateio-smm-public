import numpy as np
from numba import njit
from numba.types import Array, bool_, int64, float64
from numpy.typing import NDArray

@njit(fastmath=True)
def nbisin(a: Array, b: Array) -> Array:
    out = np.empty(a.size, dtype=bool_)
    b = set(b)

    for i in range(a.size):
        out[i] = True if a[i] in b else False

    return out



class Orderbook:
    def __init__(self, size: int) -> None:
        self.size = size
        self.asks = np.zeros((0, 2), dtype=np.float64)
        self.bids = np.zeros((0, 2), dtype=np.float64)
        self.bba = np.zeros((2, 2), dtype=np.float64)  # Initialize with correct shape

    def sort_bids(self):
        if self.bids.size > 0:
            #self.bids = self.bids[self.bids[:, 0].argsort()][: self.size]
            self.bids = self.bids[self.bids[:, 0].argsort()][::-1][: self.size]

            self.bba[0, :] = self.bids[0]
        else:
            self.bba[0, :] = [0, 0]

    def sort_asks(self):
        if self.asks.size > 0:
            self.asks = self.asks[self.asks[:, 0].argsort()][: self.size]
            self.bba[1, :] = self.asks[0]
        else:
            self.bba[1, :] = [0, 0]

    def update_bids(self, bids: Array) -> None:
        """
        if the size t
        
        """

        if bids.size == 0:
            return None
        
        self.bids = self.bids[~nbisin(self.bids[:, 0], bids[:, 0])]
        self.bids = np.vstack((self.bids, bids[bids[:, 1] != 0]))
        self.sort_bids()

    def update_asks(self, asks: Array) -> None:
        """
        Updates the current asks with new data. Removes entries with matching
        prices in update, regardless of size, and then adds non-zero quantity
        data from update to the book.

        Parameters
        ----------
        asks : Array
            New ask orders data, formatted as [[price, size], ...].
        """
        if asks.size == 0:
            return None

        self.asks = self.asks[~nbisin(self.asks[:, 0], asks[:, 0])]
        self.asks = np.vstack((self.asks, asks[asks[:, 1] != 0]))
        self.sort_asks()
            
    def update_book(self, bids: Array, asks: Array) -> None:
        """
        Updates the current orderbook with new data. Removes entries with
        matching prices in update, regardless of size, and then adds non-zero
        quantity data from update to the book.

        Parameters
        ----------
        bids : Array
            New bid orders data, formatted as [[price, size], ...].
        asks : Array
            New ask orders data, formatted as [[price, size], ...].
        """
        self.update_bids(bids)
        self.update_asks(asks)

    def get_spread(self) -> float:
        """
        Returns the current spread of the orderbook.
        """
        return self.bba[1, 0] - self.bba[0, 0]
    
    def get_mid_price(self) -> float:
        """
        Returns the mid price of the orderbook.
        """
        return (self.bba[0, 0] + self.bba[1, 0]) / 2



    



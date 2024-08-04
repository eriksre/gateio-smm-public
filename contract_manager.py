from typing import Callable

class ContractParams:
    def __init__(self, contract: str, max_long: float, max_short: float, 
                 default_long_size: float, default_short_size: float):
        self.contract = contract
        self.max_long = max_long
        self.max_short = max_short
        self.current_position = 0.0
        self.default_long_size = default_long_size
        self.default_short_size = default_short_size
        self.positive_quote_distance_bps = 10  # Default value, can be changed
        self.negative_quote_distance_bps = 10  # Default value, can be changed

    def long_reduction_func(self) -> float:
        if 0 <= self.current_position <= self.max_long:
            return 10 - (self.current_position * 0.1)
        return self.default_long_size

    def short_reduction_func(self) -> float:
        if self.max_short <= self.current_position <= 0:
            return -10 - (self.current_position * 0.1)
        return -self.default_short_size

    def update_position(self, new_position: float):
        self.current_position = new_position

    def set_quote_distances(self, positive_bps: float, negative_bps: float):
        self.positive_quote_distance_bps = positive_bps
        self.negative_quote_distance_bps = negative_bps
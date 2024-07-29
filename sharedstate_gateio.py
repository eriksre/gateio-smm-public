from get_gateio import GetGateio
from ws_gateio import WSGateio


#note size is depth of orderbook
class GateioState:
    def __init__(self, size: int) -> None:
        self.size = size
        self.get = GetGateio()
        self.ws = WSGateio()
        self.depth = "20"

    pass

#implement logic



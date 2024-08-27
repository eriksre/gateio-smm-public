from dataclasses import dataclass

@dataclass
class BaseEndpoint:
    get = "https://api.gateio.ws"
    ws = "wss://fx-ws.gateio.ws/v4/ws/usdt"

@dataclass
class GetLinks:
    orderbook = "/api/v4/futures/usdt/order_book"
    get_positions = "/api/v4/futures/usdt/positions"
    futures_tickers = "/api/v4/futures/usdt/tickers" #lists all info about all futures tickers. funding rate, mark price etc
    open_orders = "/api/v4/futures/usdt/orders"  # New endpoint for open orders

@dataclass
class PostLinks:
    cancel_all_open_orders = "/api/v4/futures/usdt/price_orders" #can't get this to work
    cancel_order_batch = "/api/v4/futures/usdt/batch_cancel_orders"
    cancel_single_order = "/api/v4/futures/usdt/orders/{order_id}"
    cancel_order_batch = "/api/v4/futures/usdt/batch_cancel_orders"

    create_order_single = "/api/v4/futures/usdt/orders"
    create_order_batch = "/api/v4/futures/usdt/batch_orders"


@dataclass
class WSLinks:
    ping = "futures.ping"
    pong = "futures.pong"

    #public
    orderbook_update = "futures.order_book_update"
    orderbook = "futures.order_book" #not supported. use orderbook_update instead. old framework with gateio
    ticker = "futures.ticker"
    public_trades = "futures.trades"
    candlesticks = "futures.candlesticks"

    #private
    user_orders = "futures.autoorders"
    user_trades = "futures.usertrades"
    user_balances = "futures.balances"


import asyncio
import websockets
from endpoints_gateio import BaseEndpoint, WSLinks
import orjson
import os
import time
import hmac
import hashlib


class WSGateio:
    def __init__(self) -> None:
        self.base_endpoint = BaseEndpoint()
        self.ws_links = WSLinks()
        self.depth = "20"
        self.subscriptions = []
        self.message_callback = None
        # Get API keys from environment variables
        self.api_key = os.getenv('gateio_api_key')
        self.api_secret = os.getenv('gateio_secret_key')

    async def _send_ping(self, interval, event):
        while not event.wait(interval):
            self.last_ping_tm = time.time()
            if self.sock:
                try:
                    self.sock.ping()
                except Exception as ex:
                    print(ex)
                    break
                try:
                    self._request("", auth_required=False)
                except Exception as e:
                    raise e
    
    async def subscribe_public_trades(self, contract: str) -> None:
        ws_url = self.base_endpoint.ws
        async with websockets.connect(ws_url) as websocket:
            subscribe_msg = {
                "time": int(time.time()),
                "channel": self.ws_links.public_trades,
                "event": "subscribe",
                "payload": [contract]
            }
            await websocket.send(orjson.dumps(subscribe_msg))
            
            try:
                response = await websocket.recv()
                print(f"Subscription response: {response}")
                
                while True:
                    message = await websocket.recv()
                    if self.message_callback:
                        self.message_callback(orjson.loads(message))
                    else:
                        print(f"Received: {message}")
            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
            except Exception as e:
                print(f"Error: {e}")
                await websocket.close()
                raise e
            
    async def subscribe_candlesticks(self, interval: str, contract: str) -> None:
        if interval not in ["10s", "1m", "5m"]:
            raise ValueError("Interval must be either '10s', '1m' or '5m'")
        ws_url = self.base_endpoint.ws
        async with websockets.connect(ws_url) as websocket:
            subscribe_msg = {
                "channel": self.ws_links.candlesticks,
                "event": "subscribe",
                "payload": [interval, contract]
            }
            await websocket.send(orjson.dumps(subscribe_msg))
            
            try:
                while True:
                    recv = await websocket.recv()
                    recv_json = orjson.loads(recv)
                    
                    # Check if the message is a candlestick update
                    if isinstance(recv_json, dict) and recv_json.get('channel') == 'futures.candlesticks':
                        print(f"Candlestick update: {recv_json}")
                    else:
                        print(f"Received: {recv_json}")

            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
            
            except Exception as e:
                print(f"Error: {e}")
                await websocket.close()
                raise e

            
    async def subscribe_orderbooks(self) -> None:
        ws_url = self.base_endpoint.ws
        async with websockets.connect(ws_url) as websocket:
            for contract in self.subscriptions:
                subscribe_msg = {
                    "channel": self.ws_links.orderbook_update,
                    "event": "subscribe",
                    "payload": [contract, "20ms", self.depth]
                }
                await websocket.send(orjson.dumps(subscribe_msg))

            try:
                while True:
                    recv = await websocket.recv()
                    recv_json = orjson.loads(recv)
                    if self.message_callback:
                        self.message_callback(recv_json)
                    else:
                        print(f"Received: {recv_json}")

            except websockets.ConnectionClosed:
                print("WebSocket connection closed")

            except Exception as e:
                print(f"Error: {e}")
                await websocket.close()
                raise e

    def add_orderbook_subscription(self, contract: str) -> None:
        self.subscriptions.append(contract)

    async def start_subscriptions(self) -> None:
        await self.subscribe_orderbooks()

    #open user orders
    # async def subscribe_user_orders(self):
    #     ws_url = self.base_endpoint.ws
    #     req = {
    #         "time": int(time.time()),
    #         "channel": self.ws_links.orders,
    #         "event": "subscribe",
    #         "payload": ["!all", "!all"],
    #         "auth": {
    #             "method": "api_key",
    #             "KEY": self.api_key,
    #             "SIGN": self.generate_signature()
    #         }
    #     }
    #     async with websockets.connect(ws_url) as websocket:
    #         await websocket.send(orjson.dumps(req))
    #         response = await websocket.recv()
    #         print(f"Subscription response: {response}")
            
    #         while True:
    #             message = await websocket.recv()
    #             if self.message_callback:
    #                 self.message_callback(orjson.loads(message))
    #             else:
    #                 print(f"Received order update: {message}")

    # def get_sign(self, message: str) -> str:
    #     return hmac.new(self.api_secret.encode("utf8"), message.encode("utf8"), hashlib.sha512).hexdigest()



    async def subscribe_user_trades(self):
        ws_url = self.base_endpoint.ws
        current_time = int(time.time())
        message = f'channel={self.ws_links.user_trades}&event=subscribe&time={current_time}'
        subscription = {
            "time": current_time,
            "channel": self.ws_links.user_trades,
            "event": "subscribe",
            "payload": ["!all"],
            "auth": {
                "method": "api_key",
                "KEY": self.api_key,
                "SIGN": self.get_sign(message),
            }
        }
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(orjson.dumps(subscription))
            while True:
                message = orjson.loads(await websocket.recv())
                if message.get("event") == "subscribe":
                    print("Subscribed to User Trades")
                elif message.get("event") == "update":
                    if self.message_callback:
                        await self.message_callback(message)
                    else:
                        contracts_and_sizes = [[item["contract"], float(item["size"])] for item in message.get("result", [])]
                        print(f"User trade update: {contracts_and_sizes}")



    async def subscribe_user_orders(self):
        ws_url = self.base_endpoint.ws
        current_time = int(time.time())
        message = f'channel={self.ws_links.user_orders}&event=subscribe&time={current_time}'
        subscription = {
            "time": current_time,
            "channel": self.ws_links.user_orders,
            "event": "subscribe",
            "payload": ["!all"],
            "auth": {
                "method": "api_key",
                "KEY": self.api_key,
                "SIGN": self.get_sign(message),
            }
        }
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(orjson.dumps(subscription))
            while True:
                message = await websocket.recv()
                if self.message_callback:
                    self.message_callback(orjson.loads(message))
                else:
                    print(f"Received user order update: {message}")

    async def subscribe_user_balances(self):
        ws_url = self.base_endpoint.ws
        current_time = int(time.time())
        message = f'channel={self.ws_links.user_balances}&event=subscribe&time={current_time}'
        subscription = {
            "time": current_time,
            "channel": self.ws_links.user_balances,
            "event": "subscribe",
            "payload": ["!all"],
            "auth": {
                "method": "api_key",
                "KEY": self.api_key,
                "SIGN": self.get_sign(message),
            }
        }
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(orjson.dumps(subscription))
            while True:
                message = await websocket.recv()
                if self.message_callback:
                    self.message_callback(orjson.loads(message))
                else:
                    print(f"Received user balance update: {message}")

async def main():
    gate_ws = WSGateio()
    
    # Add subscriptions for orderbook
    gate_ws.add_orderbook_subscription("BTC_USDT")
    gate_ws.add_orderbook_subscription("ETH_USDT")

    # Create tasks for all subscriptions
    orderbook_task = asyncio.create_task(gate_ws.subscribe_orderbooks())
    #user_orders_task = asyncio.create_task(gate_ws.subscribe_user_orders())
    # user_trades_task = asyncio.create_task(gate_ws.subscribe_user_trades())
    #public_trades_task = asyncio.create_task(gate_ws.subscribe_public_trades("BTC_USDT"))
    #public_trades_task2 = asyncio.create_task(gate_ws.subscribe_public_trades("ETH_USDT"))
    #user_balances = asyncio.create_task(gate_ws.subscribe_user_balances())
    #candlesticks = asyncio.create_task(gate_ws.subscribe_candlesticks("10s", "ETH_USDT"))


    # Wait for all tasks to complete
    await asyncio.gather(
        orderbook_task
    )

if __name__ == "__main__":
    asyncio.run(main())
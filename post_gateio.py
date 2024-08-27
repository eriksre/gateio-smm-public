import aiohttp
import json
from endpoints_gateio import BaseEndpoint, GetLinks, PostLinks
import asyncio
import os
from dotenv import load_dotenv
from auth_gateio import AuthGateio
import asyncio

class PostGateio:
    def __init__(self):
        self.base_endpoint = BaseEndpoint()
        self.get_links = GetLinks()
        self.post_links = PostLinks()
        self.base_url = self.base_endpoint.get

        load_dotenv()  # Load environment variables from .env file
        # Get API keys from environment variables
        api_key = os.getenv('gateio_api_key')
        api_secret = os.getenv('gateio_secret_key')
        
        if not api_key or not api_secret:
            raise ValueError("API key or secret not found in .env file")
        
        self.auth = AuthGateio(api_key, api_secret)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()


    # # endpoint does not seem to work. POTENTIALLY DEPRICATED DO NOT USE THIS METHOD
    # async def cancel_all_orders(self):
    #     url = self.post_links.cancel_all_open_orders
    #     headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    #     query_param = ''

    #     sign_headers = self.auth.gen_sign('DELETE', url, query_param)
    #     headers.update(sign_headers)

    #     full_url = f"{self.base_endpoint.get}{url}"
        
    #     async with self.session.delete(full_url, headers=headers) as response:
    #         return await response.json()
    
        

    # async def cancel_single_order(self, order_id: str):
    #     url = self.post_links.cancel_single_order.format(order_id=order_id)
    #     headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    #     query_param = ''
    #     sign_headers = self.auth.gen_sign('DELETE', url, query_param)
    #     headers.update(sign_headers)

    #     full_url = f"{self.base_endpoint.get}{url}"
        
    #     async with self.session.delete(full_url, headers=headers) as response:
    #         return await response.json()

    # async def create_single_order(self, contract: str, size: float, price: float, side: str, order_type: str = 'limit', text: str = '', iceberg: int = 0, tif: str = 'gtc', stp_act: str = '-'):
    #     url = self.post_links.create_order_single
    #     headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        
    #     payload = self.create_order_payload(
    #         contract=contract,
    #         size=size,
    #         price=price,
    #         side=side,
    #         order_type=order_type,
    #         text=text,
    #         iceberg=iceberg,
    #         tif=tif,
    #         stp_act=stp_act
    #     )
        
    #     body = json.dumps(payload)
    #     sign_headers = self.auth.gen_sign('POST', url, '', body)
    #     headers.update(sign_headers)

    #     async with self.session.post(f"{self.base_url}{url}", headers=headers, data=body) as response:
    #         return await response.json()

        
    @staticmethod
    def create_order_payload(contract: str, size: float, price: float, side: str, order_type: str = 'limit', text: str = '', iceberg: int = 0, tif: str = 'gtc', stp_act: str = '-'):
        return {
            "contract": contract,
            "size": size,
            "price": str(price),
            "tif": tif,
            "side": side,
            "type": order_type,
            "iceberg": iceberg,
            "text": text,
            "stp_act": stp_act
        }
    
    async def create_order_batch(self, orders_data: list):
        if len(orders_data) > 20:
            raise ValueError("Can only create up to 20 orders in a batch")

        url = self.post_links.create_order_batch
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        orders = [self.create_order_payload(**order) for order in orders_data]
        payload = json.dumps(orders)
        sign_headers = self.auth.gen_sign('POST', url, '', payload)
        headers.update(sign_headers)

        async with self.session.post(f"{self.base_url}{url}", headers=headers, data=payload) as response:
            return await response.json()
        

    #this works, but cleaner implementation is above
    # async def create_order_batch(self, orders_data: list):
    #     if len(orders_data) > 20:
    #         raise ValueError("Can only create up to 20 orders in a batch")

    #     url = self.post_links.create_order_batch
    #     headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    #     orders = [self.create_order_payload(**order) for order in orders_data]
    #     payload = json.dumps(orders)
    #     sign_headers = self.auth.gen_sign('POST', url, '', payload)
    #     headers.update(sign_headers)

    #     async with self.session.post(f"{self.base_url}{url}", headers=headers, data=payload) as response:
    #         raw_response = await response.json()
    #         processed_response = []
    #         for order in raw_response:
    #             if order.get('succeeded', False):
    #                 processed_response.append({
    #                     'contract': order['contract'],
    #                     'size': order['size'],
    #                     'price': order['price'],
    #                     'side': 'buy' if float(order['size']) > 0 else 'sell',
    #                     'text': order['text'],
    #                     'order_id': order['id']
    #                 })
    #             else:
    #                 raise Exception(f"Order creation failed: {order}")
    #         return processed_response
        

    async def cancel_order_batch(self, order_ids: list):
        if len(order_ids) > 20:
            raise ValueError("Can only cancel up to 20 orders in a batch")

        url = self.post_links.cancel_order_batch
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        
        body = json.dumps(order_ids)
        sign_headers = self.auth.gen_sign('POST', url, '', body)
        headers.update(sign_headers)

        async with self.session.post(f"{self.base_url}{url}", headers=headers, data=body) as response:
            return await response.json()


import time
#write this in the order submission class
if __name__ == "__main__":
    async def main():
        async with PostGateio() as gateio:
            order_data = {
                "contract": "BTC_USDT",
                "size": 1,
                "price": "50000",
                "side": "buy",
                "text": "t-test-order"
            }
            time.sleep(5)
            teem = time.time() 
            print(f"time: {teem}")

            result = await gateio.create_order_batch([order_data])
            print("Order submission result:")
            print(json.dumps(result, indent=2))

    asyncio.run(main())



# Used for testing
# async def main():
#     async with PostGateio() as gateio:
#         # Test batch order cancellation
#         order_ids = ["502468244728", "502468244723", "502468165203", "502468165201"]  # Replace with actual order IDs
#         result = await gateio.cancel_order_batch(order_ids)
#         print("Batch order cancellation result:", result)

# if __name__ == "__main__":
#     asyncio.run(main())

# # Main script for testing
# async def main():
#     async with PostGateio() as gateio:
#         # Test batch order creation
#         create_orders_data = [
#             {"contract": "BTC_USDT", "size": -1.5, "price": "55000", "side": "sell", "text": "t-my-custom-id-1"}
#             #{"contract": "BTC_USDT", "size": -1, "price": "65000", "side": "sell", "text": "t-my-custom-id-2"}
#         ]
#         create_result = await gateio.create_order_batch(create_orders_data)
#         print("Batch order creation result:", create_result)

#         # # Extract order IDs from the creation result (assuming the API returns them)
#         # order_ids = [order['id'] for order in create_result if 'id' in order]

#         # # Test batch order cancellation
#         # if order_ids:
#         #     cancel_result = await gateio.cancel_orders_batch(order_ids)
#         #     print("Batch order cancellation result:", cancel_result)
#         # else:
#         #     print("No orders to cancel")

# if __name__ == "__main__":
#     asyncio.run(main())

# Batch order creation result: [{'refu': 0, 'tkfr': '0.00048', 'mkfr': '0.0002', 'contract': 'BTC_USDT', 'id': 511490407262, 'price': '55000', 'tif': 'gtc', 'iceberg': 0, 'text': 't-my-custom-id-1', 'user': 14678126, 'is_reduce_only': False, 'is_close': False, 'is_liq': False, 'fill_price': '0', 'create_time': 1722755162.057, 'update_time': 1722755162.057, 'status': 'open', 'left': 1, 'refr': '0', 'size': 1, 'biz_info': '-', 'amend_text': '-', 'stp_act': '-', 'stp_id': 0, 'succeeded': True, 'update_id': 1, 'pnl': '0', 'pnl_margin': '0'}, {'refu': 0, 'tkfr': '0.00048', 'mkfr': '0.0002', 'contract': 'BTC_USDT', 'id': 511490407265, 'price': '65000', 'tif': 'gtc', 'iceberg': 0, 'text': 't-my-custom-id-2', 'user': 14678126, 'is_reduce_only': False, 'is_close': False, 'is_liq': False, 'fill_price': '0', 'create_time': 1722755162.057, 'update_time': 1722755162.057, 'status': 'open', 'left': -1, 'refr': '0', 'size': -1, 'biz_info': '-', 'amend_text': '-', 'stp_act': '-', 'stp_id': 0, 'succeeded': True, 'update_id': 1, 'pnl': '0', 'pnl_margin': '0'}]

# async def main():
#     async with PostGateio() as gateio:
#         # Test cancel all orders
#         contract = "BTC_USDT"  # Replace with the desired contract
        
#         cancel_result = await gateio.cancel_all_orders(contract)
#         print(f"Cancel all orders result for {contract}:")
#         print(json.dumps(cancel_result, indent=2))

# if __name__ == "__main__":
#     import asyncio
#     import json
#     asyncio.run(main())


# async def main():
#     async with PostGateio() as gateio:
#         result = await gateio.cancel_all_orders()
#         print("Cancel all orders result:")
#         print(json.dumps(result, indent=2))

# if __name__ == "__main__":
#     import asyncio
#     import json
#     asyncio.run(main())
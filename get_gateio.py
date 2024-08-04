import aiohttp
from endpoints_gateio import BaseEndpoint, GetLinks
import asyncio
import os
from dotenv import load_dotenv
from auth_gateio import AuthGateio

class GetGateio:
    def __init__(self):
        self.base_endpoint = BaseEndpoint()
        self.get_links = GetLinks()
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

    async def get_orderbook(self, contract: str, depth: int):
        url = f"{self.base_endpoint.get}{self.get_links.orderbook}"
        query_param = {'contract': contract, 'limit': depth, 'with_id': 'true'}
        print("getting orderbook for:", contract)

        async with self.session.get(url, params=query_param) as response:
            return await response.json()

    async def get_positions(self):
        url = self.get_links.get_positions
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        query_param = ''
        sign_headers = self.auth.gen_sign('GET', url, query_param)
        headers.update(sign_headers)

        async with self.session.get(f"{self.base_endpoint.get}{url}", headers=headers) as response:
            response_json = await response.json()
            return [[entry['contract'], entry['size']] for entry in response_json]

    async def get_futures_tickers(self):
        url = f"{self.base_endpoint.get}{self.get_links.futures_tickers}"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        async with self.session.get(url, headers=headers) as response:
            return await response.json()

    async def get_open_orders(self, contract: str = None):
        url = self.get_links.open_orders
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        query_param = 'status=open'
        if contract:
            query_param += f'&contract={contract}'
        sign_headers = self.auth.gen_sign('GET', url, query_param)
        headers.update(sign_headers)

        full_url = f"{self.base_endpoint.get}{url}?{query_param}"
        
        async with self.session.get(full_url, headers=headers) as response:
            return await response.json()

# Used for testing
async def main():
    async with GetGateio() as gateio:
        # futures_tickers = await gateio.get_open_orders("BTC_USDT")
        # print(futures_tickers)

        current_positions = await gateio.get_positions()
        print(current_positions)

if __name__ == "__main__":
    asyncio.run(main())










# [{'value': '28.5993', 'leverage': '0', 'mode': 'single', 'realised_point': '0', 'contract': 'BTC_USDT', 'entry_price': '57141.8', 'mark_price': '57198.6', 'history_point': '0', 'realised_pnl': '-0.013714032', 'close_order': None, 'size': 5, 'cross_leverage_limit': '10', 'pending_orders': 0, 'adl_ranking': 5, 'maintenance_rate': '0.004', 'unrealised_pnl': '0.0284', 'pnl_pnl': '0', 'pnl_fee': '-0.013714032', 'pnl_fund': '0', 'user': 14678126, 'leverage_max': '125', 'history_pnl': '0', 'risk_limit': '1000000', 'margin': '46.87680406619', 'last_close_pnl': '0', 'liq_price': '0', 'update_time': 1720783541, 'update_id': 1, 'initial_margin': '0', 'maintenance_margin': '0', 'open_time': 1720783541, 'trade_max_size': '0'}, 
#  {'value': '30.7187', 'leverage': '0', 'mode': 'single', 'realised_point': '0', 'contract': 'ETH_USDT', 'entry_price': '3071.7', 'mark_price': '3071.87', 'history_point': '0', 'realised_pnl': '-0.01474416', 'close_order': None, 'size': 1, 'cross_leverage_limit': '10', 'pending_orders': 0, 'adl_ranking': 5, 'maintenance_rate': '0.005', 'unrealised_pnl': '0.0017', 'pnl_pnl': '0', 'pnl_fee': '-0.01474416', 'pnl_fund': '0', 'user': 14678126, 'leverage_max': '100', 'history_pnl': '0', 'risk_limit': '1000000', 'margin': '47.09302364119', 'last_close_pnl': '0', 'liq_price': '0', 'update_time': 1720783653, 'update_id': 1, 'initial_margin': '0', 'maintenance_margin': '0', 'open_time': 1720783653, 'trade_max_size': '0'}]

[{'value': '0', 'leverage': '0', 'mode': 'single', 'realised_point': '0', 'contract': 'BTC_USDT', 'entry_price': '0', 'mark_price': '60792.47', 'history_point': '0', 'realised_pnl': '0', 'close_order': None, 'size': 0, 'cross_leverage_limit': '10', 'pending_orders': 0, 'adl_ranking': 6, 'maintenance_rate': '0.004', 'unrealised_pnl': '0', 'pnl_pnl': '0', 'pnl_fee': '0', 'pnl_fund': '0', 'user': 14678126, 'leverage_max': '125', 'history_pnl': '5.265599075704', 'risk_limit': '1000000', 'margin': '0', 'last_close_pnl': '-0.005834344', 'liq_price': '0', 'update_time': 1722765089, 'update_id': 9, 'initial_margin': '0', 'maintenance_margin': '0', 'open_time': 0, 'trade_max_size': '0'}, {'value': '29.112', 'leverage': '0', 'mode': 'single', 'realised_point': '0', 'contract': 'ETH_USDT', 'entry_price': '3071.7', 'mark_price': '2911.2', 'history_point': '0', 'realised_pnl': '-0.1605438148', 'close_order': None, 'size': 1, 'cross_leverage_limit': '10', 'pending_orders': 0, 'adl_ranking': 5, 'maintenance_rate': '0.005', 'unrealised_pnl': '-1.605', 'pnl_pnl': '0', 'pnl_fee': '-0.01474416', 'pnl_fund': '-0.1457996548', 'user': 14678126, 'leverage_max': '100', 'history_pnl': '0', 'risk_limit': '1000000', 'margin': '55.105055269094', 'last_close_pnl': '0', 'liq_price': '0', 'update_time': 1722762289, 'update_id': 1, 'initial_margin': '0', 'maintenance_margin': '0', 'open_time': 1720783653, 'trade_max_size': '0'}]
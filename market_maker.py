import asyncio
from post_gateio import PostGateio
from oms_gateio import OrderManagerGateio
from order_submission_gateio import OrderSubmissionGateio
from quote_gen_gateio import QuoteGenerator
from typing import List

class TradingExecutor:
    def __init__(self, order_submission: OrderSubmissionGateio, quote_generator: QuoteGenerator):
        self.order_submission = order_submission
        self.quote_generator = quote_generator
        self.running = False

    async def handle_quote_update(self, contract: str):
        # Cancel existing orders for the contract
        await self.cancel_existing_orders(contract)
        
        # Submit new orders based on the latest quotes
        await self.submit_new_orders(contract)

    async def cancel_existing_orders(self, contract: str):
        # Get all live orders for the contract
        live_orders = self.order_submission.get_live_orders(contract)
        
        if live_orders:
            order_ids = [order['order_id'] for order in live_orders]
            
            # Cancel the orders
            cancelled_orders = await self.order_submission.cancel_bulk_orders(order_ids)
            
            # Log the cancellation
            print(f"Cancelled {len(cancelled_orders)} orders for {contract}")

    async def submit_new_orders(self, contract: str):
        # Get the latest quotes for the contract
        quotes = self.quote_generator.current_quotes[contract]
        
        # Prepare the order data
        orders_data = []
        
        if quotes['buy_size'] != 0:
            orders_data.append({
                "contract": contract,
                "size": quotes['buy_size'],
                "price": str(quotes['buy_price']),
                "side": "buy"
            })
        
        if quotes['sell_size'] != 0:
            orders_data.append({
                "contract": contract,
                "size": quotes['sell_size'],
                "price": str(quotes['sell_price']),
                "side": "sell"
            })
        
        if orders_data:
            # Submit the orders
            created_orders = await self.order_submission.submit_bulk_orders(orders_data)
            
            # Log the new orders
            print(f"Submitted {len(created_orders)} new orders for {contract}")

    async def run(self):
        self.running = True
        while self.running:
            for contract in self.quote_generator.contracts:
                await self.handle_quote_update(contract)
            
            # Wait for a short time before the next iteration
            #await asyncio.sleep(1)  # Adjust this value as needed

    async def stop(self):
        self.running = False

async def main():
    # Define the contracts we want to trade
    contracts: List[str] = ["AERO_USDT"]

    # Initialize PostGateio
    post_gateio = PostGateio()

    # Initialize OrderManagerGateio
    order_manager = OrderManagerGateio()

    # Create OrderSubmissionGateio
    async with OrderSubmissionGateio(post_gateio, order_manager) as order_submission:
        # Set up QuoteGenerator
        quote_generator = QuoteGenerator(contracts, orderbook_depth=20)

        # Set parameters for each contract in QuoteGenerator
        for contract in contracts:
            params = quote_generator.contract_params[contract]
            params.set_quote_distances(40, 40)  # 10 bps away from mid price
            params.set_adjustment_thresholds(5, 5)  # Update quotes if 5 bps change
            params.set_price_rounding_precision(4)  # Round to 2 decimal places
            params.set_quote_best_bid_ask(False, False)  # Don't quote at best bid/ask
            params.set_enable_quotes(True, True)  # Enable both buy and sell quotes
            params.set_price_step(0.01)  # Minimum price increment

        # Create TradingExecutor
        trading_executor = TradingExecutor(order_submission, quote_generator)

        # Start the quote generator
        quote_generator_task = asyncio.create_task(quote_generator.run())

        # Start the trading executor
        trading_executor_task = asyncio.create_task(trading_executor.run())

        try:
            # Run until interrupted
            await asyncio.gather(quote_generator_task, trading_executor_task)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await trading_executor.stop()
            await quote_generator.cleanup()
            # Add any other necessary cleanup

if __name__ == "__main__":
    asyncio.run(main())




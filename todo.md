Current implementation plan:


What is needed?
- try cancelling order based on custom text id. they say operations on custom id can only be checked when order is in the orderbook. does this mean that I can't cancel if an order is pending? ie jitter send 2 req's really quick to test this out. can only do for so long after order is placed??
- if works, add a way to cancel all orders based on custom id, taking into account time since order was placed, and cancelling by order id after a certain time???
- use quanto_multiplier to know how much 1 size of a contract is worth. integrate with order_submission_gateio to do sizing based on more consistent value.
- clean up order submission such that it won't throw a fit when an order is filled, and cancellation attempted (maybe send api req to check order status if attempt fails??, though will screw with rate limits a lot)
- add in sub-class if inventory manager, to note down markouts for a given trade, and save to csv
- look through quote gen code and clean up
- look through order submission code and clean up


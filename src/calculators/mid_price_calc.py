
from dtypes import ExchangeState

class MidPriceCalc(object):
	""" Calculates a reference price based off the mid.
	"""

	def __init__(self):
		self.is_done = False
		self.price = None

	def is_ready(self):
		""" Returns a boolean indicating if the price is considered stable.
			This is relevant for pricing models that take multiple prices to
			get ready.
		"""
		return self.is_done

	def get_price(self):
		""" Returns the current calculated price whether ready or not. Initially,
			the price is None.
		"""
		return self.price

	def update_price(self, exchange_state: ExchangeState):
		""" Updates the current price in the calculator and returns the calculated
			result whether the it is ready or not for use.
		"""
		if exchange_state and exchange_state.orderbooks:
			orderbook = exchange_state.orderbooks.get(exchange_state.symbol)
			if orderbook:
				bid_price = ask_price = None
				try:
					bid_price = orderbook.bids.items()[-1][0]
					ask_price = orderbook.asks.items()[0][0]
					mid_price = float(bid_price + ask_price) / 2

					# Kollider's raw prices are decimal-place-shifted ints
					dp = exchange_state.tradable_symbols[exchange_state.symbol].price_dp
					if not dp:
						dp = 0
					self.price = mid_price * (10**-dp)

					# print(f"Got bid {bid_price}, ask {ask_price}, mid {mid_price}, and calc'd {self.price}")

					self.is_done = True
				except IndexError as e:
					print (f"Did not have a bid or ask price in orderbook: {e}")
		return self.price
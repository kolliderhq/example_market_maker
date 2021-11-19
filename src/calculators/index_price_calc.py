
from dtypes import ExchangeState

class IndexPriceCalc(object):
	""" Calculates a reference price based off the index price.
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
		if exchange_state and exchange_state.index_values:
			index_price = exchange_state.index_values.get(exchange_state.index_symbol)
			if index_price:
				self.is_done = True
				self.price = index_price.value
		return self.price
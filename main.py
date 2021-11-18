from uuid import uuid4
from ws_msg_parser import parse_msg
from kollider_api_client.ws import *
from dtypes import *
import random
from decimal import Decimal

import json
from time import sleep, time



def contract_qty_to_btc(contract_qty, price, is_inverse_priced, contract_size):
	# for quantos, this assumes that (price * contract_size) == satoshis per contract
	if is_inverse_priced:
		return contract_qty / price
	else:
		# 100_000_000 == satoshis per BTC
		return (contract_qty * price * contract_size) / 100_000_000
	
def toNearest(num, tickSize):
    """Given a number, round it to the nearest tick. Very useful for sussing float error
       out of numbers: e.g. toNearest(401.46, 0.01) -> 401.46, whereas processing is
       normally with floats would give you 401.46000000000004.
       Use this after adding/subtracting/multiplying numbers."""
    tickDec = Decimal(str(tickSize))
    return float((Decimal(round(num / tickSize, 0)) * tickDec))

class OrderManager(KolliderWsClient):
	def __init__(self, conf):
		super(OrderManager, self).__init__()
		self.conf = conf
		self.target_symbol = conf["symbol"]
		self.index_symbol = conf["index_symbol"]
		self.exchange_state = ExchangeState("kollider")
		self.exchange_state.symbol = self.target_symbol
		self.exchange_state.index_symbol = conf["index_symbol"]

		self.start_price_ask = None
		self.start_price_bid = None

	def on_message(self, _, msg):
		parse_msg(self.exchange_state, msg)
	
	def get_order_size_decay(self, interval, index):
		return int(interval * (self.conf["trading_params"]['order_size_decay']**index))

	def update_start_prices(self):
		# Making our reference price the current index price of the trade contract.
		# You could change this to your own reference price. 
		reference_price = self.exchange_state.index_values.get(self.index_symbol)

		if not reference_price:
			print("Doesn't have reference price.")
			return None

		tradable_symbol = self.exchange_state.tradable_symbols.get(self.target_symbol)

		if not tradable_symbol:
			print("Doesn't have tradable symbol.")
			return None

		tick_size = tradable_symbol.tick_size

		# self.start_price_bid = reference_price.value - tick_size
		# self.start_price_ask = reference_price.value + tick_size

		self.start_price_bid = reference_price.value * (1 - self.conf['trading_params']['offset_pct'])
		self.start_price_ask = reference_price.value * (1 + self.conf['trading_params']['offset_pct'])
		# print (f"start prices: {reference_price.value} to {self.start_price_bid} {self.start_price_ask}")

		# Back off if our spread is too small.
		min_spread = self.conf['trading_params']['min_spread']
		if self.start_price_bid * (1.00 + min_spread) > self.start_price_ask:
			self.start_price_bid *= (1.00 - (min_spread / 2))
			self.start_price_ask *= (1.00 + (min_spread / 2))

		return True

	def get_order_price(self, index, side):
		"""This creates the order stack from the starting prices given a side and index."""

		trading_params = conf["trading_params"]
		start_price = self.start_price_bid if side == "Bid" else self.start_price_ask
		# First positions (index 1, -1) should start right at start_position, others should branch from there
		index = index - 1 if side == "Ask" else -(index - 1)

		# If we're attempting to sell, but our sell price is actually lower than the buy,
		# move over to the sell side.
		if index > 0 and start_price < self.start_price_bid:
			start_price = self.start_price_ask
		# Same for buys.
		if index < 0 and start_price > self.start_price_ask:
			start_price = self.start_price_bid

		tradable_symbol = self.exchange_state.tradable_symbols.get(self.target_symbol)
		if not tradable_symbol:
			return None

		tick_size = tradable_symbol.tick_size

		order_price = toNearest(start_price + index * start_price * conf["trading_params"]["stack_pct"], tick_size)
		return order_price

	# def get_price_offset(self, index, side):
	# 	"""This creates the order stack from the starting prices given a side and index."""

	# 	trading_params = conf["trading_params"]
	# 	if trading_params['maintain_spread']:
	# 		start_price = self.start_price_bid if side == "Bid" else self.start_price_ask
	# 		# First positions (index 1, -1) should start right at start_position, others should branch from there
	# 		index = index - 1 if side == "Ask" else -(index - 1)
	# 	else:
	# 		# Offset mode: ticker comes from a reference exchange and we define an offset.
	# 		start_price = self.start_price_bid if index < 0 else self.start_price_ask

	# 		# If we're attempting to sell, but our sell price is actually lower than the buy,
	# 		# move over to the sell side.
	# 		if index > 0 and start_price < self.start_price_bid:
	# 			start_price = self.start_price_ask
	# 		# Same for buys.
	# 		if index < 0 and start_price > self.start_price_ask:
	# 			start_price = self.start_price_bid

	# 	tradable_symbol = self.exchange_state.tradable_symbols.get(self.target_symbol)
	# 	if not tradable_symbol:
	# 		return None

	# 	tick_size = tradable_symbol.tick_size

	# 	offset = toNearest(start_price * (1 + conf["trading_params"]["price_decay"]) ** index, tick_size)
	# 	return offset

	def build_order(self, index, side):
		"""Create an order object."""
		trading_params = conf["trading_params"]
		if trading_params['is_random_order_size'] is True:
			quantity = random.randint(trading_params["min_order_size"], trading_params["max_order_size"])
		else:
			quantity = trading_params['start_order_size'] + \
				trading_params['order_step_size'] * (abs(index) - 1)

		price = self.get_order_price(index, side)
		order = OpenOrder()
		order.price = price
		order.side = side
		order.symbol = self.target_symbol
		order.margin_type = "Isolated"
		order.settlement_type = "Delayed"
		order.order_type = "Limit"
		order.ext_order_id = str(uuid4())
		order.timestamp = int(time())
		order.leverage = 100
		order.quantity = quantity # in contract qty (vs "value")

		return order

	# def build_order(self, index, side):
	# 	"""Create an order object."""
	# 	trading_params = conf["trading_params"]
	# 	if trading_params['is_random_order_size'] is True:
	# 		quantity = random.randint(trading_params["min_order_size"], trading_params["max_order_size"])
	# 	else:
	# 		quantity = trading_params['start_order_size'] + \
	# 			(self.get_order_size_decay(
	# 				trading_params['order_step_size'], (abs(index) - 1)))

	# 	price = self.get_price_offset(index, side)
	# 	order = OpenOrder()
	# 	order.price = price
	# 	order.side = side
	# 	order.symbol = self.target_symbol
	# 	order.margin_type = "Isolated"
	# 	order.settlement_type = "Delayed"
	# 	order.order_type = "Limit"
	# 	order.ext_order_id = str(uuid4())
	# 	order.timestamp = int(time())
	# 	order.leverage = 100
	# 	order.quantity = quantity # in contract qty (vs "value")

	# 	return order

	def place_orders(self):
		buy_orders = []
		sell_orders = []

		if self.update_start_prices() is False:
			return

		long_btc_remaining = self.long_btc_remaining()
		short_btc_remaining = self.short_btc_remaining()

		trading_prams = self.conf["trading_params"]

		for i in range(1, trading_prams["n_levels"] + 1):

			if long_btc_remaining > 0:
				buy_order = self.build_order(i, 'Bid')
				buy_order.quantity = int(buy_order.quantity)
				if buy_order.quantity > 0:
					buy_orders.append(buy_order)

			if short_btc_remaining > 0:
				sell_order = self.build_order(i, 'Ask')
				sell_order.quantity = int(sell_order.quantity)
				if sell_order.quantity > 0:
					sell_orders.append(sell_order)	

		buy_orders = list(reversed(buy_orders))
		sell_orders = list(reversed(sell_orders))

		if self.conf["enable_dry_run"] and (len(buy_orders) > 0 or len(sell_orders)):
			print ("Dry run. Would place the following orders:")
			for sell in sell_orders:
				print (f"{sell.side} {sell.quantity} @ price {sell.price}")
			for buy in reversed(buy_orders):
				print (f"{buy.side} {buy.quantity} @ price {buy.price}")
		else:
			return self.converge_orders(buy_orders, sell_orders)

	def converge_orders(self, buy_orders, sell_orders):
		# Covering and quoting on price is somewhat independent.
		to_amend = []
		to_create = []
		to_cancel = []
		buys_matched = 0
		sells_matched = 0
		existing_orders = self.exchange_state.open_orders.get(self.target_symbol)
		if not existing_orders:
			existing_orders = []

		tradable_symbol = self.exchange_state.tradable_symbols.get(self.target_symbol)
		if not tradable_symbol:
			return None 

		bid_orders = sorted(existing_orders, key=lambda order: order.price)
		ask_orders = sorted(
			existing_orders, key=lambda order: order.price, reverse=True)

		bid_orders = [order for order in bid_orders if order.side == "Bid"]
		ask_orders = [order for order in ask_orders if order.side == "Ask"]
		existing_orders = bid_orders + ask_orders

		# Check all existing orders and match them up with what we want to place.
		# If there's an open one, we might be able to amend it to fit what we want.

		trading_params = conf["trading_params"]
		# Bid orders should be order from lowest to highest and ask orders should be from highest to lowest.
		level_indices = 2 * list(range(0, trading_params["n_levels"]))[::-1]

		for index, order in enumerate(existing_orders):
			# logger.info("Existing Orders found.")
			try:
				if order.side == 'Bid':
					desired_order = buy_orders[buys_matched]
					buys_matched += 1
				else:
					desired_order = sell_orders[sells_matched]
					sells_matched += 1

				# Found an existing order. Do we need to amend it?
				remaining_quantity = order.quantity - order.filled
				level_index = level_indices[index]
				if desired_order.quantity != remaining_quantity or (
						# If price has changed, and the change is more than our RELIST_INTERVAL, amend.
						desired_order.price != order.price and
						abs((desired_order.price / order.price) - 1) > trading_params["relist_tollerance"]):
					open_order = OpenOrder()
					open_order.price = desired_order.price
					open_order.quantity = desired_order.quantity
					open_order.side = order.side
					open_order.order_id = order.order_id
					open_order.symbol = order.symbol
					open_order.settlement_type = "Delayed"
					open_order.timestamp = int(time())
					to_amend.append(open_order)
			except IndexError:
				# Will throw if there isn't a desired order to match. In that case, cancel it.
				to_cancel.append(order)
			
		while buys_matched < len(buy_orders):
			to_create.append(buy_orders[buys_matched])
			buys_matched += 1

		while sells_matched < len(sell_orders):
			to_create.append(sell_orders[sells_matched])
			sells_matched += 1

		if len(to_amend) > 0:
			for order in to_amend:
				dp = tradable_symbol.price_dp
				order.price = int(order.price * (10**dp))
				self.cancel_order(order.to_dict())
				self.place_order(order.to_dict())

		if len(to_create) > 0:
			for order in reversed(to_create):
				dp = tradable_symbol.price_dp
				order.price = int(order.price * (10**dp))
				self.place_order(order.to_dict())

		if len(to_cancel) > 0:
			for order in reversed(to_cancel):
				dp = tradable_symbol.price_dp
				order.price = int(order.price * (10**dp))
				self.cancel_order(order.to_dict())
	
	def short_btc_remaining(self):
		# Returns unsigned value in BTC
		max_short_pos_btc = self.conf["trading_params"]["max_short_pos_btc"]
		if not self.conf["check_position_limits"]:
			return max_short_pos_btc
		position = self.exchange_state.positions.get(self.target_symbol)
		contract = self.exchange_state.tradable_symbols.get(self.target_symbol)
		if position:
			if position.entry_price != 0:
				position_btc = contract_qty_to_btc(position.quantity,
					position.entry_price, contract.is_inverse_priced,
					contract.contract_size)
				if position.side == "Bid":
					return max_short_pos_btc + position_btc
				else:
					return max_short_pos_btc - position_btc
		return max_short_pos_btc

	def long_btc_remaining(self):
		# Returns unsigned value in BTC
		max_long_pos_btc = self.conf["trading_params"]["max_long_pos_btc"]
		if not self.conf["check_position_limits"]:
			return max_long_pos_btc
		position = self.exchange_state.positions.get(self.target_symbol)
		contract = self.exchange_state.tradable_symbols.get(self.target_symbol)
		if position:
			if position.entry_price != 0:
				position_btc = contract_qty_to_btc(position.quantity,
					position.entry_price, contract.is_inverse_priced,
					contract.contract_size)
				if position.side == "Ask":
					return max_long_pos_btc + position_btc
				else:
					return max_long_pos_btc - position_btc
		return max_long_pos_btc

	def run(self):
		# Connecting to the Kollider sockets.
		self.connect(self.conf["ws_url"], self.conf["api_key"], self.conf["api_secret"], self.conf["api_passphrase"])
		# Give the sockets some time to connect.
		sleep(2)
		# Subscribing to index prices.
		self.sub_index_price([self.conf["index_symbol"]])
		self.sub_position_states()
		# Fetching symbols that are available to trade.
		self.fetch_tradable_symbols()
		self.fetch_positions()
		self.fetch_open_orders()
		self.fetch_symbols()
		self.who_am_i()

		while True:
			sleep(1)
			success = self.update_start_prices()
			if not success:
				continue
			self.place_orders()



if __name__ in "__main__":
	conf = None
	with open("config.json",) as f:
		conf = json.load(f)
	om = OrderManager(conf)
	om.run()
import uuid
from BTrees.OOBTree import OOBTree
import copy

class ExchangeState(object):

    def __init__(self, venue_name):
        self.positions = {}
        self.open_orders = {}
        self.balances = {}
        self.mark_prices = {}
        self.index_values = {}
        self.tradable_symbols = {}
        self.whoami = {}
        self.price_tickers = {}
        self.orderbooks = {}
        self.venue_name = venue_name
        self.is_authenticated = False
        self.symbol = None
        self.index_symbol = None

    def to_dict(self):
        return {
            "whoami": self.whoami,
            "balances": self.balances,
            "index_values": self.index_values,
            "is_authenticated": self.is_authenticated,
        }

class IndexValue(object):
	def __init__(self):
		self.value = 0
		self.symbol = ""
		self.dnom = ""

def parse_index_value(msg=None):
    index_value = IndexValue()
    if msg:
        index_value.value = float(msg["value"])
        index_value.symbol = msg["symbol"]
        index_value.denom = msg["denom"]
    return index_value

class Order(object):
    symbol = ""
    quantity = 0
    leverage = 100
    price = 0
    order_type = ""
    margin_type = "Isolated"
    settlement_type = "Delayed"
    side = ""
    ext_order_id = str(uuid.uuid4())

    def to_dict(self):
        return {
            "type": "order",
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "leverage": self.leverage,
            "price": self.price,
            "order_type": self.order_type,
            "margin_type": self.margin_type,
            "settlement_type": self.settlement_type,
            "ext_order_id": self.ext_order_id
        }

class CancelOrder(object):
    symbol = ""
    order_id = 0
    settlement_type = "Delayed"

    def to_dict(self):
        return {
            "type": "cancel_order",
            "symbol": self.symbol,
            "order_id": self.order_id,
            "settlement_type": self.settlement_type,
        }

class TradableSymbol(object):
    def __init__(self):
        self.base_margin = 0
        self.contract_size = 0
        self.is_inverse_priced = None
        self.last_price = 0
        self.maintenance_margin = 0
        self.max_leverage = 0
        self.price = 0
        self.symbol = ""
        self.underlying_symbol = ""
        self.tick_size = 0
        self.lot_size = 1
        self.maker_fee = 0
        self.taker_fee = 0

def parse_tradable_symbols(msg=None):
    tradable_symbols = TradableSymbol()
    if msg:
        tradable_symbols.base_margin = float(msg["base_margin"])
        tradable_symbols.contract_size = int(msg["contract_size"])
        tradable_symbols.is_inverse_priced = msg["is_inverse_priced"]
        tradable_symbols.last_price = float(msg["last_price"])
        tradable_symbols.maintenance_margin = float(msg["maintenance_margin"])
        tradable_symbols.max_leverage = float(msg["max_leverage"])
        tradable_symbols.price_dp = int(msg["price_dp"])
        tradable_symbols.symbol = msg["symbol"]
        tradable_symbols.underlying_symbol = msg["underlying_symbol"]
        tradable_symbols.tick_size = float(msg["tick_size"])
    return tradable_symbols

class OpenOrder(object):

    def __init__(self):
        self.ext_order_id = str(uuid.uuid4())
        self.quantity = 0
        self.order_id = 0
        self.price = 0
        self.timestamp = ""
        self.filled = 0
        self.order_type = ""
        self.side = ""
        self.symbol = ""
        self.leverage = 100
        self.margin_type = ""
        self.settlement_type = ""

    def to_dict(self):
        return {
            "quantity": self.quantity,
            "order_id": self.order_id,
            "price": self.price,
            "timestamp": self.timestamp,
            "filled": self.filled,
            "ext_order_id": self.ext_order_id,
            "order_type": self.order_type,
            "side": self.side,
            "symbol": self.symbol,
            "leverage": self.leverage,
            "margin_type": self.margin_type,
            "settlement_type": self.settlement_type
        }

def parse_open_order(msg=None, dp=None):
    open_order = OpenOrder()
    if msg:
        if not dp:
            dp = 0
        open_order.quantity = int(msg["quantity"])
        open_order.order_id = int(msg["order_id"])
        open_order.price = float(msg["price"]) * (10**-dp)
        open_order.timestamp = msg["timestamp"]
        open_order.filled = int(msg["filled"])
        open_order.ext_order_id = int(msg["order_id"])
        open_order.order_type = msg["order_type"]
        open_order.side = msg["side"]
        open_order.symbol = msg["symbol"]
        open_order.leverage = float(msg["leverage"])
        open_order.margin_type = msg["margin_type"]
        open_order.settlement_type = msg["settlement_type"]
    return open_order

class Position(object):
    def __init__(self):
        self.symbol = ""
        self.quantity = 0
        self.entry_price = 0
        self.leverage = 0
        self.liq_price = 0
        self.open_order_ids = []
        self.side = ""
        self.timestamp = ""
        self.upnl = 0
        self.rpnl = 0

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "leverage": self.leverage,
            "liq_price": self.liq_price,
            "side": self.side,
            "timestamp": self.timestamp,
            "upnl": self.upnl,
            "rpnl": self.rpnl,
        }

def parse_position(msg=None):
    position = Position()
    if msg:
        position.symbol = msg["symbol"]
        position.quantity = int(msg["quantity"])
        position.entry_price = float(msg["entry_price"])
        position.leverage = float(msg["leverage"])
        position.liq_price = float(msg["liq_price"])
        position.open_order_ids = msg["open_order_ids"]
        position.side = msg["side"]
        position.timestamp = msg["timestamp"]
        position.upnl = int(msg["upnl"])
        position.rpnl = float(msg["rpnl"])
    return position

class Orderbook(object):

    def __init__(self, venue):
        self.bids = copy.copy(OOBTree())
        self.asks = copy.copy(OOBTree())
        self.level = "l2"
        self.venue = venue
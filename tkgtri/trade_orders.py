
from .orderbook import OrderBook


class OrderError(Exception):
    """Basic exception for errors raised by cars"""
    pass


class OrderResult:
    def __init__(self):
        self.id = ""

        self.amount = 0 # result amopunt if buy than base, if sell than quoote
        self.asset = "" # result asset

        self.quote_amount = 0
        self.quote_asset = ""
        self.base_amount = 0

        self.response = ""

        self.commission = 0
        self.commission_asset = ""

        self.fills_depth = 0
        self.status = ""
        self.placed = False

        # 'info': response,
        # 'id': orderId,
        # 'timestamp': timestamp,
        # 'datetime': iso8601,
        # 'lastTradeTimestamp': None,
        # 'symbol': market['symbol'],
        # 'type': type,
        # 'side': side,
        # 'amount': amount,
        # 'filled': None,
        # 'remaining': None,
        # 'price': price,
        # 'cost': cost,
        # 'status': 'open',
        # 'fee': None,
        # 'trades': None,



class TradeOrder:

    # todo create wrapper constructor for fake/real orders with any starting asset
    # different wrapper constructors for amount of available asset
    # so developer have not to implement the bid calculation
    #
    # TradeOrder.fake_order_from_asset(symbol, start_asset, amount, ticker_price, order_book = None, exchange = None,
    #  commission = 0 )
    #
    # TradeOrder.order_from_asset(symbol, start_asset, amount, ticker_price, exchange )
    #

    def create_order_from_start_amount(self, symbol, amount, side, price):
        pass

    def cancel_order(self):
        pass

    def update_order_status_from_exchange_data(self):
        pass

    def get_filled_amount_in_dest(self):
        pass

    def get_filled_amount_in_source(self):
        pass

    def recover_start_currency(self):
        pass

    def __init__(self, symbol, amount, side):
        # todo add commission ?


        # if side is not None:
        #     self.side = side.upper()
        #
        # elif start_asset is not None and ticker_price is not None:
        #     self.side = "SELL" if symbol.split("/")[0] == start_asset else "BUY"
        #
        # else:
        #     raise OrderError("side or start asset are not provided ")

        self.symbol = symbol.upper()
        self.amount = amount
        self.side = side.upper()
        self.order_book = None
        self.result = OrderResult()
        self.status = str

    def fake_market_order(self, orderbook=None, exchange=None):

        if orderbook is None and exchange is None:
            raise OrderError("Orderbook or exchange are needed to be provided")

        if orderbook is not None and exchange is not None:
            raise OrderError("Provide only orderbook or exchange")

        if orderbook is not None and isinstance(orderbook, OrderBook):
            self.order_book = orderbook
        elif isinstance(orderbook, OrderBook):
            raise OrderError("Wrong order book provided")

        if orderbook is None and exchange is not None:
            ob_array = exchange.fetch_order_book(self.symbol)
            order_book = OrderBook(self.symbol, ob_array["asks"], ob_array["bids"])
            self.order_book = order_book

        depth = self.order_book.get_depth(self.amount, self.side.lower(), "base")

        if depth is not None:
            self.result.placed = True
            self.result.id = "1"
            self.result.quote_amount = depth.total_quantity
            self.result.quote_asset = depth.currency
            self.result.totalPrice = depth.total_price
            self.result.fills_depth = depth.depth

            if self.side =="SELL":
                self.result.asset = self.symbol.split("/")[1]
                self.result.amount = depth.total_quantity

            if self.side == "BUY":
                self.result.asset = self.symbol.split("/")[0]
                self.result.amount = self.amount

            return self.result

    # def get_bid_from_start_currency(self, amount):

























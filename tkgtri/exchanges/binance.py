from .. import exchange_wrapper as ew


class binance(ew.ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(binance, self).__init__(exchange_id, api_key, secret )
        self.wrapper_id = "binance"

    def _fetch_tickers(self):
        return self._ccxt.fetch_bids_asks()

    def _create_order(self, symbol, order_type, side, amount, price=None):
        # create_order(self, symbol, type, side, amount, price=None, params={})
        return self._ccxt.create_order(symbol, order_type, side, amount, price, {"newOrderRespType": "FULL"})

    def _fetch_order(self, order):
        return self._ccxt.fetch_order(order.id, order.symbol)

    def get_exchange_wrapper_id(self):
        return self.wrapper_id



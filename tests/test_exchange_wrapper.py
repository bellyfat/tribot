# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest


class ExchageWrapperTestSuite(unittest.TestCase):

    def test_create_wrapped(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "binance")
        self.assertEqual(exchange._ccxt.id, "binance")

    def test_create_generic(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "generic")
        self.assertEqual(exchange._ccxt.id, "kucoin")

    def test_fetch_ticker_wrapped(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        self.assertEqual(exchange.get_tickers()["ETH/BTC"]["last"], None)

    def test_fetch_ticker_generic(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        self.assertIsNot(exchange.get_tickers()["ETH/BTC"]["last"], None)

    def test_load_markets_from_file(self):

        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        markets = exchange.load_markets_from_json_file("test_data/markets_binance.json")

        self.assertEqual(markets["ETH/BTC"]["active"], True)

    def test_load_tickers_from_csv(self):

        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        tickers = exchange.load_tickers_from_csv("test_data/tickers_binance.csv")

        self.assertEqual(len(tickers), 3)
        self.assertEqual(tickers[2]["ETH/BTC"]["ask"], 0.082975)

    def test_init_offline_mode(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")

        self.assertEqual(exchange.offline, True)
        self.assertEqual(exchange._offline_tickers[2]["ETH/BTC"]["ask"], 0.082975)
        self.assertEqual(exchange._offline_markets["ETH/BTC"]["active"], True)


if __name__ == '__main__':
    unittest.main()
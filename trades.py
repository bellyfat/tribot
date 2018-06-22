import tkgtri
import sys
import json
import collections

_keys = {"binance":
             {"key": "O1hGc8oRK7BXfBS7ynXZPcXwjdnaz5fU5RJow9RM7sHCWfMJLgdBAnh6dopCFk5I",
              "secret": "D4ddhpjcerL4F3Hhbwjp5lly1U7UGjVg4N7iyciDf4NwDN85uy262kU3ZeVhQO3X"},
         "kucoin":
             {"key": "5b22b10709e5a14f2c125e3d",
              "secret": "11ec0073-8919-4863-a518-7e2468506752"}
         }

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("binance",
#                                              "AmEkXUlAh3fW1XkxIOSLovMVia1B55bWI2937Y9ZGRu25uJj2XSCBbOGoI8bb8II",
#                                              "6yy8vrkUR3aOBJyUkzRtEHGYR01gxMmyYJ6jMHyt3HxY7AtXlKr54FmtPOLUsBvh")

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin",
#                                              "5b22b10709e5a14f2c125e3d", "11ec0073-8919-4863-a518-7e2468506752")

exchange_id = "binance"
start_curr = "ETH"
dest_cur = "BTC"
start_curr_amount = 0.05 / 3

eW = tkgtri.ccxtExchangeWrapper.load_from_id(exchange_id, _keys[exchange_id]["key"],
                                             _keys[exchange_id]["secret"])

eW.get_markets()

balance_start_curr = eW._ccxt.fetch_balance()[start_curr]["free"]

symbol = tkgtri.core.get_symbol(start_curr, dest_cur, eW.markets)
side = tkgtri.core.get_order_type(start_curr, dest_cur, symbol)

ob_array = eW._ccxt.fetch_order_book(symbol)
ob = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array['bids'])

d = ob.get_depth_for_destination_currency(start_curr_amount, dest_cur)
price = d.total_price*0.9
amount = d.total_quantity / d.total_price if side == "sell" else d.total_quantity

order_history_file_name = tkgtri.utils.get_next_filename_index("test_data/orders/{}.json".format(eW.exchange_id))
order_resps = collections.OrderedDict()

order = tkgtri.TradeOrder.create_limit_order_from_start_amount(symbol, start_curr, start_curr_amount, dest_cur, price)

# order_resp = eW.place_limit_order(order.symbol, order.side, order.amount/3, order.price)
order_resp = eW.place_limit_order(order)
order.update_order_from_exchange_resp(order_resp)

order_resps["create"] = order_resp
order_resps["updates"] = list()

with open(order_history_file_name, 'w') as outfile:
    json.dump(order_resps, outfile, indent=4)

print("Oder id{}".format(order.id))
tick = 0

while order.status != "closed" and order.status != "canceled":
    try:
        update_resp = eW.get_order_update(order)
        order.update_order_from_exchange_resp(update_resp)
        order_resps["updates"].append(update_resp)
    except Exception as e:
        print("Exception: {}".format(type(e).__name__))
        print("Exception body:", e.args)

    finally:

        print("Tick {}: Order {} updated".format(tick, order.id))

        with open(order_history_file_name, 'w') as outfile:
            json.dump(order_resps, outfile, indent=4)

    tick += 1

sys.exit(0)
# d = ob.(bal_to_bid, dest_cur)
# price = d.total_price
# amount = d.total_quantity


pass
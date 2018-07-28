from tkgtri import TriBot
from tkgtri import Analyzer
import sys
import traceback

TriBot.print_logo("TriBot v0.5")

#
# set default parameters
#
tribot = TriBot("_config.json", "_tri.log")

tribot.report_all_deals_filename = "%s/_all_deals.csv"  # full path will be exchange_id/all_deals.csv
tribot.report_tickers_filename = "%s/all_tickers_%s.csv"
tribot.report_deals_filename = "%s/deals_%s.csv"
tribot.report_prev_tickers_filename = "%s/deals_%s_tickers.csv"

tribot.debug = True
tribot.force_best_tri = True

tribot.set_log_level(tribot.LOG_INFO)
# ---------------------------------------

tribot.log(tribot.LOG_INFO, "Started")

tribot.set_from_cli(sys.argv[1:])  # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename)  # config taken from cli or default

tribot.init_timer()
tribot.timer.notch("start")


tribot.log(tribot.LOG_INFO, "Exchange ID:" + tribot.exchange_id)
tribot.log(tribot.LOG_INFO, "session_uuid:" + tribot.session_uuid)
tribot.log(tribot.LOG_INFO, "Debug: {}".format(tribot.debug))
tribot.log(tribot.LOG_INFO, "Force trades with best result: {}".format(tribot.force_best_tri))

# now we have exchange_id from config file or cli
tribot.init_reports("_"+tribot.exchange_id+"/")

# init the remote reporting
try:
    tribot.init_remote_reports()
except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error Report DB connection {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    tribot.log(tribot.LOG_INFO, "Continue....", e.args)
try:
    tribot.init_exchange()
    tribot.load_markets()
    tribot.exchange.init_async_exchange()

except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error while exchange initialization {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    sys.exit(0)

if len(tribot.markets) < 1:
    tribot.log(tribot.LOG_ERROR, "Zero markets {}".format(tribot.exchange_id))
    sys.exit(0)

try:
    tribot.set_triangles()
except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error while preparing triangles {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    sys.exit(0)

if len(tribot.all_triangles) < 1:
    tribot.log(tribot.LOG_ERROR, "Zero basic triangles".format(tribot.exchange_id))
    sys.exit(0)

tribot.log(tribot.LOG_INFO, "Triangles found: {}".format(len(tribot.all_triangles)))

# outer main loop
while True:

    # fetching the balance for first start currency or taking test balance from the cli/config
    try:
        tribot.load_balance()
        tribot.log(tribot.LOG_INFO, "Balance: {}".format(tribot.balance))
    except Exception as e:
        tribot.log(tribot.LOG_ERROR, "Error while fetching balance {}".format(tribot.exchange_id))
        tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
        tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
        continue

    # main loop
    while True:

        if tribot.fetch_number > 0 and tribot.run_once:
            sys.exit(666)

        tribot.timer.reset_notches()

        working_triangle = dict()
        order_books = dict()
        expected_result = 0.0
        bal_to_bid = 0.0

        #
        # todo add reset all the working variables
        # todo add reporting from previous iteration on entering the fetch cycle
        #

        # exit when debugging and because of errors
        if tribot.debug is True and tribot.errors > 0:
            tribot.log(tribot.LOG_INFO, "Exit on errors, debugging")
            sys.exit(666)

        # resetting error
        tribot.errors = 0

        # fetching tickers
        try:
            tribot.timer.check_timer()
            tribot.timer.notch("time_from_start")
            tribot.fetch_tickers()
            tribot.timer.notch("duration_fetch")
            print("Tickers fetched {}".format(len(tribot.tickers)))
        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error while fetching tickers exchange_id:{} session_uuid:{} fetch_num:{} :".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number))

            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

            tribot.errors += 1
            continue  # drop the trades and return to ticker fetch loop

        # proceeding tickers
        try:
            tribot.proceed_triangles()
            tribot.tri_list_good = tribot.get_good_triangles()  # tri_list became sorted after this

            tribot.reporter.set_indicator("good_triangles", len(tribot.tri_list_good))
            tribot.reporter.set_indicator("total_triangles", len(tribot.tri_list))
            tribot.reporter.set_indicator("best_triangle", tribot.tri_list[0]["triangle"])
            tribot.reporter.set_indicator("best_result", tribot.tri_list[0]["result"])

            tribot.timer.notch("duration_proceed")

        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error while proceeding tickers exchange_id{}: session_uuid:{} fetch_num:{} :".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number))

            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)

            tribot.errors += 1
            continue

        # checking the good triangles and live flag
        if not tribot.force_best_tri and len(tribot.tri_list_good) <= 0:
            continue  # no good triangles

        if tribot.force_best_tri:
            working_triangle = tribot.tri_list[0]  # taking best triangle
            bal_to_bid = tribot.balance  # balance to bid as actual balance or test balance

        else:  # taking the best triangle and max balance to bid
            working_triangle = tribot.tri_good_list[0]  # taking best good triangle

            # get the maximum balance to bid because of result
            bal_to_bid = tribot.get_max_balance_to_bid(tribot.start_currency[0], tribot.balance,
                                                       working_triangle["result"],
                                                       working_triangle["result"])

        # fetching the order books for symbols in triangle
        try:
            tribot.log(tribot.LOG_INFO, "Try to fetch order books: {} {} {} ".format(working_triangle["symbol1"],
                                                                                     working_triangle["symbol2"],
                                                                                     working_triangle["symbol3"]))
            tribot.timer.notch("get_order_books")
            order_books = tribot.get_order_books_async(list([working_triangle["symbol1"],
                                                             working_triangle["symbol2"],
                                                             working_triangle["symbol3"]]))
            tribot.log(tribot.LOG_INFO, "Order books fetched")
        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error while fetching order books exchange_id{}: session_uuid:{}"
                                         " fetch_num:{} :"
                                         "for {}{}{}".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number, working_triangle["symbol1"],
                              working_triangle["symbol2"],working_triangle["symbol3"]))
            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
            tribot.errors += 1
            continue

        # getting the maximum amount to bid for the  first trade
        try:
            max_possible = Analyzer.get_maximum_start_amount(tribot.exchange, working_triangle,
                                                             {1: order_books[working_triangle["symbol1"]],
                                                              2: order_books[working_triangle["symbol2"]],
                                                              3: order_books[working_triangle["symbol3"]]},
                                                             bal_to_bid, 100,
                                                             tribot.min_amounts[tribot.start_currency[0]])
            bal_to_bid = max_possible["amount"]
            expected_result = max_possible["result"] + 1

        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error calc the result and amount on order books exchange_id{}: session_uuid:{}"
                                         " fetch_num:{} :"
                                         "for {}{}{}".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number, working_triangle["symbol1"],
                              working_triangle["symbol2"],working_triangle["symbol3"]))

            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
            tribot.errors += 1
            continue

        # check if need to force start amount and calc the ob result
        if tribot.force_start_amount:
            bal_to_bid = tribot.force_start_amount
            tribot.log(tribot.LOG_INFO, "Force amount to bid:{}".format(tribot.force_start_amount))
            try:
                expected_result = Analyzer.order_book_results(tribot.exchange, working_triangle,
                                                        {1: order_books[working_triangle["symbol1"]],
                                                         2: order_books[working_triangle["symbol2"]],
                                                         3: order_books[working_triangle["symbol3"]]},
                                                        bal_to_bid)["result"]
            except Exception as e:
                tribot.log(tribot.LOG_ERROR,
                           "Error calc the result and amount on order books exchange_id{}: session_uuid:{}"
                           " fetch_num:{} :""for {}{}{}".format(tribot.exchange_id, tribot.session_uuid,
                                                                tribot.fetch_number, working_triangle["symbol1"],
                                                                working_triangle["symbol2"],
                                                                working_triangle["symbol3"]))
                tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
                tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
                tribot.errors += 1
                continue

        # going to deals
        tribot.log(tribot.LOG_INFO, "Amount to bid:{}".format(bal_to_bid))
        tribot.log(tribot.LOG_INFO, "Expected result:{}".format(expected_result))

        # reporting states:
        tribot.reporter.set_indicator("session_uuid", tribot.session_uuid)
        tribot.reporter.set_indicator("fetch_number", tribot.fetch_number)
        tribot.reporter.set_indicator("errors", tribot.errors)

        tribot.reporter.push_to_influx()
        tribot.timer.notch("duration_to_influx")

        print("Fetch_num: {}".format(tribot.fetch_number))
        print("Errors: {}".format(tribot.errors))
        print("Good triangles: {} / {} ".format(len(tribot.tri_list_good),
                                                len(tribot.tri_list)))
        print("Best triangle {}: {} ".format(tribot.last_proceed_report["best_result"]["triangle"],
                                             tribot.last_proceed_report["best_result"]["result"]))
        print("Tickers proceeded {} time".format(len(tribot.tickers)))
        print("Duration,s: " + str(tribot.timer.results_dict()))
        print("====================================================================================")

tribot.log(tribot.LOG_INFO, "Total time:" + str((tribot.timer.notches[-1]["time"] - tribot.timer.start_time).total_seconds()))
tribot.log(tribot.LOG_INFO, "Finished")








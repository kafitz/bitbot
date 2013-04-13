import time
import logging
import config
import datetime
from decimal import Decimal
from observer import Observer
from private_markets import mtgox
from private_markets import bitfloor
from private_markets import bitstamp
from private_markets import btce
from private_markets import bitcoin24
from modules import control

class TraderBot(Observer):
    def __init__(self):
        print "TraderBot loaded!"
        self.mtgox = mtgox.PrivateMtGox()
        self.bitfloor = bitfloor.PrivateBitfloor()
        self.bitstamp = bitstamp.PrivateBitstamp()
        self.btce = btce.PrivateBTCe()
        self.bitcoin24 = bitcoin24.PrivateBitcoin24()
        self.clients = {
            "MtGoxUSD": self.mtgox,
            "BitfloorUSD": self.bitfloor,
            "BitstampUSD": self.bitstamp,
            "BtceUSD": self.btce,
            "Bitcoin24USD": self.bitcoin24
        }
        self.profit_thresh = config.profit_thresh   # in USD
        self.perc_thresh = config.perc_thresh                        # in %
        self.last_trade = 0
        self.timeout = 300                          # in seconds (for buying wait time before error alert)
        self.potential_trades = []
        self.priority_list = [value for key, value in self.clients.items()]

    def begin_opportunity_finder(self, depths):
        # List of exchanges that will be ignored during a deal iteration if the exchange
        # is found not to have enough balance
        self.ignore_exchange = []
        self.failed_outputs = []

    def end_opportunity_finder(self, bitbot, deals=None):
        if not deals:
            return
        # Sorts arbs list lowest profit to highest, then reverses to get the most profitable
        deals.sort(key=lambda x: x['percent_profit'], reverse=True)
        # Execute only the best arb opportunity
        self.execute_trade(bitbot, deals)

    def update_balance(self, buy_market, sell_market):
        self.clients[buy_market].get_info()
        self.clients[sell_market].get_info()

    def opportunity(self, profit, purchase_volume, buyprice, kask, sellprice, kbid, percent_profit, weighted_buyprice,
                                weighted_sellprice, available_volume, purchase_cap):
        pass


    def execute_trade(self, bitbot, deals, best_deal_index=0):
        channel = config.deal_output # set output irc channel
        start = time.time()
        # Set variables from first deal in sorted list
        if best_deal_index < len(deals):
            best_deal = deals[best_deal_index]
            trade_attempt = best_deal_index + 1
        else:
            bitbot.msg(channel, 'No trade available: '+', '.join(self.failed_outputs))
            return
        profit = best_deal['profit']
        volume = best_deal['purchase_volume']
        buy_mkt = best_deal['buy_market']
        sell_mkt = best_deal['sell_market']
        buy_price = best_deal['buy_price']
        sell_price = best_deal['sell_price']
        percent_profit = best_deal['percent_profit']

        # test 3b
        if buy_mkt in self.ignore_exchange or sell_mkt in self.ignore_exchange:
            # Already notified console & irc of failed balance check,
            # this just returns and tries again until another exchange is found
            ignored_exchanges = []
            if buy_mkt in self.ignore_exchange:
                ignored_exchanges.append(buy_mkt)
            if sell_mkt in self.ignore_exchange:
                ignored_exchanges.append(sell_mkt)
            ignore_str = ', '.join(ignored_exchanges)
            output = "#{0} - deal skipped because exchanges ignored: {1}".format(trade_attempt, ignore_str)
            self.failed_outputs.append(output)
            print output
            print self.failed_outputs
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        # test 1
        if buy_mkt not in self.clients:
            output = "#{0}: can't automate this trade, client not available: {1}".format(trade_attempt, buy_mkt)
            logging.warn(output)
            self.failed_outputs.append(output)
            print output
            print self.failed_outputs
            # If market not available, try with next best deal
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        # test 2
        if sell_mkt not in self.clients:
            output = "#{0}: can't automate this trade, client not available: {1}".format(trade_attempt, sell_mkt)
            logging.warn(output)
            self.failed_outputs.append(output)
            print output
            print self.failed_outputs
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        # test 3
        if percent_profit < config.profit_thresh:
            output = "#{0}: can't automate trade between {1} and {2}, minimum percent profit ({4:.2f}%) not reached: {3:.2f}%".format(trade_attempt, buy_mkt, sell_mkt, percent_profit, config.profit_thresh)
            logging.warn(output)
            self.failed_outputs.append(output)
            print self.failed_outputs
            return
        # test 4 - check account balances
        self.update_balance(buy_mkt, sell_mkt)
        # Get the max amount of BTC the USD at buy_mkt can purchase or the amount of BTC at the sell_mkt,
        # whichever is lowest
        try:
            buy_tradeable_amt = float(self.clients[buy_mkt].usd_balance) / ((1 + config.balance_margin) * buy_price)
            sell_tradeable_amt = float(self.clients[sell_mkt].btc_balance) / (1 + config.balance_margin)
        except TypeError:
            # Couldnt update balance of buy or sell market so balance == None
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        if buy_tradeable_amt < config.trade_amount:
            output = "#" + str(trade_attempt) + ": insufficient balance to execute trade at " + buy_mkt +\
                " USD balance: " + str(self.clients[buy_mkt].usd_balance)
            self.ignore_exchange.append(buy_mkt)
        elif sell_tradeable_amt < config.trade_amount:
            output = "#" + str(trade_attempt) + ": insufficient balance to execute trade at " + buy_mkt +\
                " USD balance: " + str(self.clients[buy_mkt].usd_balance)
            self.ignore_exchange.append(buy_mkt)
        self.failed_outputs.append(output)
        logging.warn(output)
        best_deal_index += 1
        self.execute_trade(bitbot, deals, best_deal_index)
        return

        # test 5 - trade wait time
        current_time = time.time()
        if current_time - self.last_trade < config.trade_wait:
            output = "#{0}: can't automate this trade, last trade occured {1} seconds ago".format(trade_attempt, (current_time - self.last_trade))
            logging.warn(output)
            bitbot.msg(channel, output)
            return

        end = time.time() - start
        print "TraderBot - execute trade: ", str(end)

        # Execute deals function with first (best) deal and pass along same deals list
        control.deal(best_deal_index, deals)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output =  "Deal executed at " + str(timestamp) + " -- Bought " + str(volume) + " BTC at " + buy_mkt + \
            " for $" + str(buy_price) + ", sold at " + sell_mkt + " for $" + str(sell_price) + ". Profit of $" + str(profit)
        logging.info(output)
        bitbot.msg(channel, output)
        bitbot.msg('#merlin', 'O Dear Leaders kafitz & baspt, a trade has been executed!')
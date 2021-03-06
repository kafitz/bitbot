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
from private_markets import campbx
from modules import control

class TraderBot(Observer):
    def __init__(self):
        print "TraderBot loaded!"
        self.mtgox = mtgox.PrivateMtGox()
        self.bitfloor = bitfloor.PrivateBitfloor()
        self.bitstamp = bitstamp.PrivateBitstamp()
        self.btce = btce.PrivateBTCe()
        self.bitcoin24 = bitcoin24.PrivateBitcoin24()
        self.campbx = campbx.PrivateCampBX()
        self.clients = {
            "MtGoxUSD": self.mtgox,
            "BitfloorUSD": self.bitfloor,
            "BitstampUSD": self.bitstamp,
            "BtceUSD": self.btce,
            "Bitcoin24USD": self.bitcoin24,
            "CampBXUSD": self.campbx            
        }
        self.profit_thresh = config.profit_thresh   # in USD
        self.perc_thresh = config.perc_thresh                        # in %
        self.last_trade = 0
        self.timeout = 300                          # in seconds (for buying wait time before error alert)
        self.potential_trades = []
        self.priority_list = [value for key, value in self.clients.items()]
        self.gox_lag = 0

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
        self.gox_lag = control.lag(bitbot, '.lag mtgx', output=False)
        # if self.gox_lag > 60:
        #     bitbot.msg(config.deal_output, "MtGox lag of {}, too risky to trade")
        # else:
        #     print "MtGox lag (seconds): " + str(self.gox_lag)
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
            output = 'No trades available ({0} seconds) | '.format(self.gox_lag)
            bitbot.msg(channel, output + ' | '.join(self.failed_outputs))
            return
        profit = best_deal['profit']
        volume = best_deal['purchase_volume']
        buy_mkt = best_deal['buy_market']
        sell_mkt = best_deal['sell_market']
        buy_price = best_deal['buy_price']
        sell_price = best_deal['sell_price']
        percent_profit = best_deal['percent_profit']

        # trade wait time
        current_time = time.time()
        if current_time - self.last_trade < config.trade_wait:
            time_diff = current_time - self.last_trade
            output = "too soon, last trade occured {} seconds ago".format(time_diff)
            logging.warn(output)
            bitbot.msg(channel, output)
            return

        # test 3b
        if buy_mkt in self.ignore_exchange or sell_mkt in self.ignore_exchange:
            # Already notified console & irc of failed balance check,
            # this just returns and tries again until another exchange is found
            if buy_mkt in self.ignore_exchange:
                ignored_exchange = buy_mkt
            if sell_mkt in self.ignore_exchange:
                ignored_exchange = sell_mkt
            output = "{0}. {1} ignored".format(trade_attempt, ignored_exchange)
            self.failed_outputs.append(output)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        # test 1
        if buy_mkt not in self.clients:
            output = "{0}. {1} client not available".format(trade_attempt, buy_mkt)
            logging.warn(output)
            self.failed_outputs.append(output)
            self.ignore_exchange.append(buy_mkt)
            # If market not available, try with next best deal
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        # test 2
        if sell_mkt not in self.clients:
            output = "{0}. {1} client not available".format(trade_attempt, sell_mkt)
            logging.warn(output)
            self.failed_outputs.append(output)
            self.ignore_exchange.append(sell_mkt)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        # test 3
        if percent_profit < config.profit_thresh:
            output = "{0}. {1} > {2} {3:.2f}/{4:.2f}%".format(trade_attempt, buy_mkt, sell_mkt, percent_profit, config.profit_thresh)
            logging.warn(output)
            self.failed_outputs.append(output)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
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
            output = "{0}. timeout while updating balances".format(trade_attempt)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        if buy_tradeable_amt < config.trade_amount:
            output = "{0}. {2} balance: ${1} USD".format(trade_attempt, self.clients[buy_mkt].usd_balance, buy_mkt)
            self.ignore_exchange.append(buy_mkt)
            self.failed_outputs.append(output)
            logging.warn(output)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        if sell_tradeable_amt < config.trade_amount:
            output = "{0}. {2} balance: {1} BTC".format(trade_attempt, self.clients[sell_mkt].btc_balance, sell_mkt)
            self.ignore_exchange.append(sell_mkt)
            self.failed_outputs.append(output)
            logging.warn(output)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return

        end = time.time() - start
        print "Executing trade (" + str(self.gox_lag) + "):", str(end)
            
        # Emulate input from IRC so bitbot.say continues to work in control.py
        class CommandInput(unicode):
            def __new__(cls, channel, deal_index): 
                s = unicode.__new__(cls, deal_index)
                s.sender = channel
                s.nick = bitbot.nick
                s.event = 'PRIVMSG'
                s.bytes = deal_index
                s.match = None
                s.group = None
                s.groups = None
                s.args = (channel, deal_index)
                s.admin = False
                s.owner = False
                return s
        deal_index = '.deal ' + str(best_deal_index + 1) # +1 to account for index handling in .deal function
        fake_irc_input = CommandInput(channel, deal_index)

        # Execute deals function with first (best) deal and pass along same deals list
        control.deal(bitbot, fake_irc_input, deals)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output =  "Deal executed at " + str(timestamp) + " -- Bought " + str(volume) + " BTC at " + buy_mkt + \
            " for $" + str(buy_price) + ", sold at " + sell_mkt + " for $" + str(sell_price) + ". Profit of $" + str(profit)
        logging.info(output)
        bitbot.msg(channel, output)
        self.last_trade = time.time()
        bitbot.msg('#merlin', 'baspt, kafitz: deal attempted from ' + buy_mkt + ' to ' + sell_mkt + ' (' + timestamp + ').')
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

    def irc(self, bitbot, message):
        channel = config.deal_output
        bitbot.msg(channel, message)

    def begin_opportunity_finder(self, depths):
        pass

    def end_opportunity_finder(self, bitbot, deals=None):
        if not deals:
            return
        # Sorts arbs list lowest profit to highest, then reverses to get the most profitable
        deals.sort(key=lambda x: x['percent_profit'], reverse=True)
        # Execute only the best arb opportunity
        self.execute_trade(bitbot, deals)

    def get_min_tradeable_volume(self, buyprice, usd_bal, btc_bal):
        min1 = float(usd_bal) / ((1 + config.balance_margin) * buyprice)
        min2 = float(btc_bal) / (1 + config.balance_margin)
        return min(min1, min2)

    def update_balance(self, buy_market, sell_market):
        self.clients[buy_market].get_info()
        self.clients[sell_market].get_info()

    def opportunity(self, profit, purchase_volume, buyprice, kask, sellprice, kbid, percent_profit, weighted_buyprice,
                                weighted_sellprice, available_volume, purchase_cap):
        pass


    def execute_trade(self, bitbot, deals, best_deal_index=0):
        start = time.time()
        # Set variables from first deal in sorted list
        if best_deal_index <= len(deals):
            best_deal = deals[best_deal_index]
            trade_attempt = best_deal_index + 1
        profit = best_deal['profit']
        volume = best_deal['purchase_volume']
        buy_mkt = best_deal['buy_market']
        sell_mkt = best_deal['sell_market']
        buy_price = best_deal['buy_price']
        sell_price = best_deal['sell_price']
        percent_profit = best_deal['percent_profit']
        channel = config.deal_output # set output irc channel

        if buy_mkt not in self.clients:
            output = "Attempt %d: can't automate this trade, client not available: %s" % (trade_attempt, buy_mkt)
            logging.warn(output)
            self.irc(bitbot, output)
            # If market not available, try with next best deal
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        if sell_mkt not in self.clients:
            output = "Attempt %d: can't automate this trade, client not available: %s" % (trade_attempt, sell_mkt)
            logging.warn(output)
            self.irc(bitbot, output)
            best_deal_index += 1
            self.execute_trade(bitbot, deals, best_deal_index)
            return
        if profit < config.profit_thresh:
            output = "Attempt %d: can't automate this trade, minimum percent profit not reached %f/%f" % (trade_attempt, percent_profit, config.profit_thresh)
            logging.warn(output)
            self.irc(bitbot, output)
            return
        self.update_balance(buy_mkt, sell_mkt)
        # Get the max amount of BTC the USD at buy_mkt can purchase or the amount of BTC at the sell_mkt,
        # whichever is lowest
        trade_amount = self.get_tradeable_volume(buy_price, self.clients[buy_mkt].usd_balance,
                                           self.clients[sell_mkt].btc_balance)
        if trade_amount < config.trade_amount:
            error_output = "Attempt " + str(trade_attempt) + ": insufficient balance to execute trade: " + buy_mkt +\
                " USD balance: " + str(self.clients[buy_mkt].usd_balance) + ", " +\
                sell_mkt + " BTC balance: " + str(self.clients[sell_mkt].btc_balance)
            logging.warn(error_output)
            self.irc(bitbot, error_output)
            return
        current_time = time.time()
        if current_time - self.last_trade < config.trade_wait:
            output = "Attempt %d: can't automate this trade, last trade occured %s seconds ago" % (trade_attempt, (current_time - self.last_trade))
            logging.warn(output)
            self.irc(bitbot, output)
            return

        end = time.time() - start
        print "TraderBot - execute trade: ", str(end)

        # Execute deals function with first (best) deal and pass along same deals list
        # control.deal(1, deals)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        irc_output =  "Deal executed at " + str(timestamp) + " -- Bought " + str(volume) + " BTC at " + buy_mkt + \
            " for $" + str(buy_price) + ", sold at " + sell_mkt + " for $" + str(sell_price) + ". Profit of $" + str(profit)
        self.irc(bitbot, irc_output)

        try:
            # self.watch_balances(bitbot, channel, buy_mkt, sell_mkt, volume)
            irc_output = str(timestamp) + " deal between " + buy_mkt + " and " + sell_mkt + " succeeded."
            self.irc(bitbot, irc_output)
        except:
            irc_output = "Error: Check wallets for deal at " + str(timestamp) + " between " + buy_mkt + " and " + sell_mkt + "."
            # self.irc(bitbot, irc_output)
    
    def watch_balances(self, bitbot, channel, buymarket, sellmarket, volume):
        buymarket_btc = self.clients[buymarket].btc_balance
        sellmarket_btc = self.clients[sellmarket].btc_balance
        end_btc =  buymarket_btc + Decimal(volume)
        buy_wallet_btc = 0
        runtime = 0
        print "Buy market balance:"
        while buy_wallet_btc != end_btc:
            if runtime == self.timeout:
                break
            self.clients[buymarket].get_info()
            buy_wallet_btc = self.clients[buymarket].btc_balance
            print buymarket + " BTC: " + str(buy_wallet_btc)
            self.last_trade = time.time()
            runtime += 5
            time.sleep(5)
        end_btc = sellmarket + btc
        self.clients[sellmarket].deposit()
        deposit_addr = self.client[sellmarket].address
        bitbot.msg(channel, "Transferring " + str(volume) + " to " + deposit_addr + ". http://https://blockchain.info/address/" + deposit_addr)
        self.clients[buymarket].wdw(volume, deposit_addr)
        sell_wallet_btc = 0
        runtime = 0
        sell_timeout = 3600 # Wait one hour
        print "Sell market balance:"
        while sell_wallet_btc != end_btc:
            while runtime != sell_timeout:
                break
            self.client[sellmarket].get_info()
            sell_wallet_btc = self.clients[sellmarket].btc_balance
            print sellmarket + " BTC: " + str(sell_wallet_btc)
            self.last_trade = time.time()
            runtime += 5
            time.sleep(5)
import logging
import config
import time
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
        self.perc_thresh = 1                        # in %
        self.trade_wait = 120                       # in seconds
        self.last_trade = 0
        self.timeout = 300                          # in seconds (for buying wait time before error alert)
        self.potential_trades = []
        self.priority_list = [value for key, value in self.clients.items()]

    def begin_opportunity_finder(self, depths):
        self.potential_trades = []

    def end_opportunity_finder(self, bitbot, deals):
        if not self.potential_trades:
            return
        # Sorts arbs list lowest profit to highest, then reverses to get the most profitable
        self.potential_trades.sort(key=lambda x: x[0])
        self.potential_trades.reverse()
        # Execute only the best arb opportunity
        self.execute_trade(bitbot, *self.potential_trades[0])   # * expands list to variables as called for by function

    def get_min_tradeable_volume(self, buyprice, usd_bal, btc_bal):
        min1 = float(usd_bal) / ((1 + config.balance_margin) * buyprice)
        min2 = float(btc_bal) / (1 + config.balance_margin)
        return min(min1, min2)

    def update_balance(self):
        for kclient in self.clients:
            self.clients[kclient].get_info()

    def opportunity(self, profit, purchase_volume, buyprice, kask, sellprice, kbid, percent_profit, weighted_buyprice,
                                weighted_sellprice, available_volume, purchase_cap):
        # if profit < self.profit_thresh or perc < self.perc_thresh:
        #     return
        if kask not in self.clients:
            logging.warn("Can't automate this trade, client not available: %s" % (kask))
            return
        if kbid not in self.clients:
            logging.warn("Can't automate this trade, client not available: %s" % (kbid))
            return

        # Update client balance
        self.update_balance()
        # maximum volume transaction with current balances
        min_volume = self.get_min_tradeable_volume(weighted_buyprice, self.clients[kask].usd_balance,
                                                   self.clients[kbid].btc_balance)
        # Maxme had this to control for making small trades if possible (I assume figuring the fees by hand beforehand)
        # Changed this to make the max_amount specified in config as also the minimum to execute a trade to keep things
        # simpler for now
        if min_volume < config.max_amount:
            error_output = "Insufficient balances to execute trade: " + kask +\
                " USD balance: " + str(self.clients[kask].usd_balance) + ", " +\
                kbid + " BTC balance: " + str(self.clients[kbid].btc_balance)
            logging.warn(error_output)
            # return

        volume = purchase_volume

        # self.clients[kask].last_opportunity = time.time()
        # # Create a list of exchange objects sorted by last available trade (most recent --> least recent)
        # self.priority_list.sort(key=lambda x: x.last_opportunity, reverse=True)
        # print self.priority_list


        if profit < config.profit_thresh:
            logging.warn("Can't automate this trade, minimum percent profit not reached %f/%f"
                         % (percent_profit, config.profit_thresh))
            return

        current_time = time.time()
        if current_time - self.last_trade < self.trade_wait:
            logging.warn("Can't automate this trade, last trade occured %s seconds ago" % (
                current_time - self.last_trade))
            return

        self.potential_trades.append([profit, volume, kask, kbid, weighted_buyprice, weighted_sellprice])

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


    def execute_trade(self, bitbot, profit, volume, kask, kbid, weighted_buyprice, weighted_sellprice):
        channel = config.deal_output
        self.last_trade = time.time()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        irc_output =  "Deal executed at " + str(timestamp) + " -- Bought " + str(volume) + " BTC at " + kask + \
            " for $" + str(weighted_buyprice) + ", sold at " + kbid + " for $" + str(weighted_sellprice) + ". Profit of $" + str(profit)
        bitbot.msg(channel, irc_output)
        # self.clients[kask].buy(volume, weighted_buyprice)
        # self.clients[kbid].sell(volume, weighted_buyprice)
        try:
            self.watch_balances(bitbot, channel, kask, kbid, volume)
            irc_output = str(timestamp) + " deal between " + kask + " and " + kbid + " succeeded."
            bitbot.msg(channel, irc_output)
        except:
            irc_output = "Error: Check wallets for deal at " + str(timestamp) + " between " + kask + " and " + kbid + "."
        #     bitbot.msg(channel, irc_output)
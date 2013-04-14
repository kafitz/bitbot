import public_markets
import observers
import config
import time
import datetime
import logging
import json
import threading

class Arbitrer(object):
    def __init__(self, suppress_observers=False):
        self.markets = []
        self.observers = []
        self.depths = {}
        self.init_markets(config.markets)
        if not suppress_observers:
            self.init_observers(config.observers)
        self.deals = []

    def init_markets(self, markets):
        self.market_names = markets
        for market_name in markets:
            exec('import public_markets.' + market_name.lower())
            market = eval('public_markets.' + market_name.lower() + '.' + market_name + '()')
            self.markets.append(market)

    def init_observers(self, observers):
        self.observer_names = observers
        for observer_name in observers:
            exec('import observers.' + observer_name.lower())
            observer = eval('observers.' + observer_name.lower() + '.' + observer_name + '()')
            self.observers.append(observer)

    def get_profit_for(self, selling_index, buying_index, kask, kbid):
        # check to make sure input buying price actually lower than selling price
        if self.depths[kask]['asks'][selling_index]['price'] >= self.depths[kbid]['bids'][buying_index]['price']:
            return 0, 0, 0, 0, 0 

        # get the maximum amount of asks or bids that can current be filled by
        # the market within our spread
        max_amount_buy = 0
        for i in range(selling_index + 1):
            max_amount_buy += self.depths[kask]['asks'][i]['amount']
        max_amount_sell = 0
        for j in range(buying_index + 1):
            max_amount_sell += self.depths[kbid]['bids'][j]['amount'] 
        
        if float(self.depths[kask]['asks'][i]['price']) == 0:
            return 0, 0, 0, 0, 0
        max_amount = min(max_amount_buy, max_amount_sell, config.trade_amount)
        buy_total = 0
        w_buyprice = 0
        total_available_volume = 0
        # For as long as we have bitcoin available, look for transactions we can make
        for i in range(selling_index + 1):
            price = self.depths[kask]['asks'][i]['price']
            amount = min(max_amount, buy_total + self.depths[kask]['asks'][i]['amount']) - buy_total
            total_available_volume += self.depths[kask]['asks'][i]['amount']
            if amount <= 0:
                break
            buy_total += amount
            if w_buyprice == 0: # Set the buy price on the first run
                w_buyprice = price
            else:
                w_buyprice = (w_buyprice * (buy_total - amount) + price * amount) / buy_total
        sell_total = 0
        w_sellprice = 0
        for j in range(buying_index + 1):
            price = self.depths[kbid]['bids'][j]['price']
            amount = min(max_amount, sell_total + self.depths[kbid]['bids'][j]['amount']) - sell_total
            if amount <= 0:
                break
            sell_total += amount
            if w_sellprice == 0:
                w_sellprice = price
            else:
                w_sellprice = (w_sellprice * (sell_total - amount) + price * amount) / sell_total

        profit = sell_total * w_sellprice - buy_total * w_buyprice
        return profit, sell_total, w_buyprice, w_sellprice, total_available_volume

    def get_max_depth(self, kask, kbid):
        i = 0
        if len(self.depths[kbid]['bids']) != 0 and len(self.depths[kask]['asks']) != 0:
            # Create a list of the indices of selling offer key/pairs (price, volume) that are less than the current max buying offer
            while self.depths[kask]['asks'][i]['price'] < self.depths[kbid]['bids'][0]['price']:
                if i >= len(self.depths[kask]['asks']) - 1:
                    break
                i += 1
        j = 0
        if len(self.depths[kask]['asks']) != 0 and len(self.depths[kbid]['bids']) != 0:
            # Create a list of the indices of buying offer key/pairs that are less than the current maxium selling offer
            while self.depths[kask]['asks'][0]['price'] < self.depths[kbid]['bids'][j]['price']:
                if j >= len(self.depths[kbid]['bids']) - 1:
                    break
                j += 1
        max_selling_index = i
        max_buying_index = j
        return max_selling_index, max_buying_index

    def arbitrage_depth_opportunity(self, kask, kbid):
        # Get the maximum index of the overlap
        max_selling_indices, max_buying_indices = self.get_max_depth(kask, kbid)
        best_profit = 0
        best_selling_index, best_buying_index = (0, 0)
        best_w_buyprice, best_w_sellprice = (0, 0)
        best_volume = 0
        for selling_index in range(max_selling_indices + 1):
            for buying_index in range(max_buying_indices + 1):
                profit, volume, w_buyprice, w_sellprice, total_available_volume = self.get_profit_for(selling_index, buying_index, kask, kbid)
                if profit >= 0 and profit >= best_profit:
                    best_profit = profit
                    best_volume = volume
                    best_w_buyprice, best_w_sellprice = (w_buyprice, w_sellprice)
                    best_selling_index, best_buying_index = (selling_index, buying_index)
                    available_volume = total_available_volume
        # Account for transaction fees
        buying_fees = self.fees[kask]
        selling_fees = self.fees[kbid]
        sale_total = best_volume * best_w_sellprice 
        buy_total = best_volume * best_w_buyprice
        tx_fee_discount = 1 - float(selling_fees['exchange_rate'])
        # Fix divide by 0 error
        if buy_total == 0:
            return 0, 0, 0, 0, 0, 0, 0, 0
        percent_profit = ((sale_total * tx_fee_discount) / buy_total - 1) * 100
        fee_adjusted_profit = (sale_total * tx_fee_discount) - buy_total
        return fee_adjusted_profit, best_volume, percent_profit, self.depths[kask]['asks'][best_selling_index]['price'],\
            self.depths[kbid]['bids'][best_buying_index]['price'], best_w_buyprice, best_w_sellprice, round(available_volume,1)

    def arbitrage_opportunity(self, kask, ask, kbid, bid):
        profit, purchase_volume, percent_profit, buyprice, sellprice, weighted_buyprice,\
            weighted_sellprice, available_volume = self.arbitrage_depth_opportunity(kask, kbid)
        if purchase_volume == 0 or buyprice == 0:
            return
        
        if percent_profit < float(config.perc_thresh):
            return
        buy_total = round(purchase_volume * weighted_buyprice, 1)
        
        for observer in self.observers:
            observer.opportunity(profit, purchase_volume, buyprice, kask, sellprice, kbid, percent_profit, weighted_buyprice,
                                weighted_sellprice, available_volume, config.trade_amount)
        
        # Line to return to IRC
        line_tuple = (profit, purchase_volume, available_volume, buy_total, kask, weighted_buyprice, weighted_sellprice, kbid, percent_profit)
        deal = {'profit': profit, 'purchase_volume': purchase_volume, 'buy_market': kask, 'buy_price': weighted_buyprice, 'sell_market': kbid, \
            'sell_price': weighted_sellprice, 'percent_profit': percent_profit}
        self.deals.append(deal) 
        return line_tuple

    def update_depths(self):
        depths = {}
        fees = {}
        threads = []
        def scrape(market):
            start = time.time()
            depths[market.name] = market.get_depth()
            update = str(time.time() - start)
            print market.name + " update time: " + update

        for market in self.markets:
            thread = threading.Thread(target=scrape, args=(market,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        for market in self.markets:
            fees[market.name] = market.fees
        return depths, fees

    def tickers(self):
        for market in self.markets:
            try:
                logging.debug('ticker: ' + market.name + ' - ' + str(market.get_ticker()))
            except:
                logging.debug('error: unable to get ticker for ' + market.name)

    def replay_history(self, directory):
        import os
        import json
        import pprint
        files = os.listdir(directory)
        files.sort()
        for f in files:
            depths = json.load(open(directory + '/' + f, 'r'))
            self.depths = {}
            for market in self.market_names:
                if market in depths:
                    self.depths[market] = depths[market]
            self.tick()

    def tick(self, bitbot, channel, deal_call=False):
        for observer in self.observers:
            observer.begin_opportunity_finder(self.depths)

        # Lists for output string formatting
        line_tuples = []
        longest_buy_market = 0
        longest_sell_market = 0
        longest_volume = 0
        longest_buy_price = 0
        longest_sell_price = 0

        for kmarket1 in self.depths:
            for kmarket2 in self.depths:
                if kmarket1 == kmarket2:  # same market
                    continue
                market1 = self.depths[kmarket1]
                market2 = self.depths[kmarket2]
                if len(market1['asks']) > 0 and len(market2['bids']) > 0:
                    if float(market1['asks'][0]['price']) < float(market2['bids'][0]['price']):
                        line_tuple = None
                        line_tuple = self.arbitrage_opportunity(kmarket1, market1['asks'][0], kmarket2, market2['bids'][0])
                        if line_tuple:
                            line_tuples.append(line_tuple)
                            # Get longest lengths of line elements for string formatting
                            if len(str(line_tuple[4])) > longest_buy_market:
                                longest_buy_market = len(str(line_tuple[4]))
                            if len(str(line_tuple[7])) > longest_sell_market:
                                longest_sell_market = len(str(line_tuple[7]))
                            if len(str(line_tuple[2])) > longest_volume:
                                longest_volume = len(str(round(line_tuple[2], 2)))
                            if len(str(round(line_tuple[5], 3))) > longest_buy_price:
                                longest_buy_price = len(str(round((line_tuple[5]), 3)))
                            if len(str(round(line_tuple[6], 3))) > longest_sell_price:
                                longest_sell_price = len(str(round((line_tuple[6]), 3)))
                                               
        print longest_buy_price                     
        if not deal_call and line_tuples != []:
            line_tuples.sort(key=lambda x: x[8], reverse=True) # sort deals best --> worst
            deal_index = 1
            for line_tuple in line_tuples:
                profit, purchase_volume, available_volume, buy_total, kask, weighted_buyprice,\
                    weighted_sellprice, kbid, percent_profit = line_tuple
                weighted_buyprice = '${0:.3f}'.format(weighted_buyprice)
                weighted_sellprice = '${0:.3f}'.format(weighted_sellprice)
                line = '#{deal_index} ${0:.2f} | {1:.2f} of {2:' '>{vwidth}} BTC for ${3:.2f} | {4:' '<{mk1width}} {5:>{bwidth}} => {6:>{swidth}} {7:' '<{mk2width}} | {8:>{pwidth}.2f}%'.format(\
                    profit, purchase_volume, available_volume, buy_total, kask, weighted_buyprice,
                    weighted_sellprice, kbid, percent_profit, deal_index=deal_index, mk1width=longest_buy_market,
                    vwidth=longest_volume, bwidth=longest_buy_price, swidth=longest_sell_price, mk2width=longest_sell_market, pwidth=4)
                bitbot.msg(channel, line)
                deal_index += 1
            bitbot.msg(channel, '-' * len(line)) # '----' page break line_tuple'

        self.deals.sort(key=lambda x: x['percent_profit'], reverse=True)
        if not deal_call:
            for observer in self.observers:
                observer.end_opportunity_finder(bitbot, self.deals)
        return


    def loop(self, bitbot):
        level = logging.INFO
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)
        channel = config.arbitrage_output
        deal_call = False

        while True:
            self.deals = []
            start = time.time()
            self.depths, self.fees = self.update_depths()
            end = time.time() - start
            print "TraderBot - updating depths: ", str(end)

            self.tickers()

            start = time.time()
            self.tick(bitbot, channel, deal_call)
            end = time.time() - start
            print "TraderBot - tick: ", str(end)

            time.sleep(60)
            
    def get_arb(self, bitbot):
        level = logging.INFO
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)
        channel = config.deal_output
        deal_call = True

        self.depths, self.fees = self.update_depths()
        self.tickers()
        self.tick(bitbot, channel, deal_call)
        self.deals.sort(key=lambda x: x['percent_profit'], reverse=True)
        return self.deals


if __name__ == '__main__':
    print __doc__.strip()

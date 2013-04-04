import public_markets
import observers
import config
import time
import datetime
import logging
import json


class Arbitrer(object):
    def __init__(self):
        self.markets = []
        self.observers = []
        self.depths = {}
        self.init_markets(config.markets)
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
        max_amount = min(max_amount_buy, max_amount_sell, config.max_amount)
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
        fee_adjusted_volume = (1 - float(buying_fees['exchange_rate'])) * best_volume # Volume2*adjusted volume; Volume1*original volume
        sale_total = fee_adjusted_volume * best_w_sellprice 
        buy_total = best_volume * best_w_buyprice
        tx_fee_discount = 1 - float(selling_fees['exchange_rate'])
        # Fix divide by 0 error
        if buy_total == 0:
            return 0, 0, 0, 0, 0, 0, 0, 0
        percent_profit = ((sale_total * tx_fee_discount) / buy_total - 1) * 100
        fee_adjusted_profit = (sale_total * tx_fee_discount) - buy_total
        return fee_adjusted_profit, fee_adjusted_volume, percent_profit, self.depths[kask]['asks'][best_selling_index]['price'],\
            self.depths[kbid]['bids'][best_buying_index]['price'], best_w_buyprice, best_w_sellprice, round(available_volume,1)

    def arbitrage_opportunity(self, kask, ask, kbid, bid):
        profit, purchase_volume, percent_profit, buyprice, sellprice, weighted_buyprice,\
            weighted_sellprice, available_volume = self.arbitrage_depth_opportunity(kask, kbid)
        if purchase_volume == 0 or buyprice == 0:
            return
        
        if percent_profit < float(config.perc_thresh):
            return
        for observer in self.observers:
            observer.opportunity(profit, purchase_volume, available_volume, buy_total, kask, weighted_buyprice, 
                                weighted_sellprice, kbid, percent_profit, config.max_amount)
        # Line to return to IRC
        buy_total = round(purchase_volume * weighted_buyprice, 1)
        line_output = '${0:.2f} | {1:.2f} of {2:.2f} BTC for ${3:.2f} | {4:11} ${5:.3f} => ${6:.3f} {7:11} | {8:.2f}%'.format(\
            profit, purchase_volume, available_volume, buy_total, kask, weighted_buyprice, weighted_sellprice, kbid, percent_profit)
        deal = {'profit': profit, 'purchase_volume': purchase_volume, 'buy_market': kask, 'buy_price': weighted_buyprice, 'sell_market': kbid, \
            'sell_price': weighted_sellprice, 'percent_profit': percent_profit}
        self.deals.append(deal) 
        return line_output

    def update_depths(self):
        depths = {}
        fees = {}
        for market in self.markets:
            depths[market.name] = market.get_depth()
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

    def tick(self):
        for observer in self.observers:
            observer.begin_opportunity_finder(self.depths)

        output_list = []
        for kmarket1 in self.depths:
            for kmarket2 in self.depths:
                if kmarket1 == kmarket2:  # same market
                    continue
                market1 = self.depths[kmarket1]
                market2 = self.depths[kmarket2]
                # spammy debug command for testing if there is no market liquidity
                # print 'Is ' + kmarket1 + ' at ' + str(market1['asks'][0]['price']) + ' less than ' + kmarket2 + ' at ' + str(market2['bids'][0]['price']) + '?'
                if len(market1['asks']) > 0 and len(market2['bids']) > 0:
                    if float(market1['asks'][0]['price']) < float(market2['bids'][0]['price']):
                        line_out = self.arbitrage_opportunity(kmarket1, market1['asks'][0], kmarket2, market2['bids'][0])
                        output_list.append(line_out)

        for observer in self.observers:
            observer.end_opportunity_finder()
        return output_list


    def loop(self, bitbot):
        level = logging.INFO
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)
        channel = config.arbitrage_output

        while True:
            self.depths, self.fees = self.update_depths()
            self.tickers()
            line_outs = self.tick()
            line_outs = filter(None, line_outs)
            if line_outs == []:
                # bitbot.msg(channel, 'arb > no opportunities found')
                pass
            else:
                for item in line_outs:
                    bitbot.msg(channel, item)
                bitbot.msg(channel, '------------------------------------------------------------------------------------------')                   
            time.sleep(60)
            
    def get_arb(self,bitbot):
        level = logging.INFO
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)
        channel = config.deal_output

        self.depths, self.fees = self.update_depths()
        self.tickers()
        line_outs = self.tick()
        line_outs = filter(None, line_outs)

        return self.deals


if __name__ == '__main__':
    print __doc__.strip()

import urllib2
import json
import logging
from market import Market

class bitfloorUSD(Market):
    def __init__(self):
        super(bitfloorUSD, self).__init__("USD")
        self.update_rate = 25
        # {withdraw: amount bitcoins charged as network fee, exchange_rate: % for currency exchange}
        self.fees = {'withdraw': 0, 'exchange_rate': 0.004}

    def update_depth(self):
        try:
            res = urllib2.urlopen('https://api.bitfloor.com/book/L2/1')
            jsonstr = res.read()
            depth = json.loads(jsonstr)
            self.depth = self.format_depth(depth)
        except Exception:
            logging.warn("Can't parse json:" + jsonstr)

    def sort_and_format(self, l, reverse=False):
        # sort list: for each dict in input list, get price key and sort by that
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        ret = []
        for i in l:
            # create a return a list of dicts sorted according to bid/ask w/ only the price and volume
            ret.append({'price': float(i[0]), 'amount': float(i[1])})
        return ret


    def format_depth(self, depth):
        # returns a dict for comparison against other exchanges in arbitrage.py:tick()
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = bitfloorUSD()
    print market.get_depth()
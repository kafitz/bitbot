import urllib2
import json
import logging
from market import Market

class BitstampUSD(Market):
    def __init__(self):
        super(BitstampUSD, self).__init__("USD")
        # bitcoin central maximum call / day = 5000
        # keep 2500 for other operations
        self.update_rate = 24 * 60 * 60 / 2500
        self.fees = {'withdraw': 0, 'exchange_rate': 0.005}

    def update_depth(self):
        try:
            res = urllib2.urlopen('https://www.bitstamp.net/api/order_book/')
            depth = json.loads(res.read())
            self.depth = self.format_depth(depth)
        except:
            self.depth = {'asks': [], 'bids': []}
            logging.error("BitstampUSD - depth data fetch error.")

    def sort_and_format(self, l, reverse):
        r = []
        for i in l:
            r.append({'price': float(i[0]), 'amount': float(i[1])})
        r.sort(key=lambda x: float(x['price']), reverse=reverse)
        return r

    def format_depth(self, depth):
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = BitstampUSD()
    print market.get_ticker()

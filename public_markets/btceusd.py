import urllib2
import json
from market import Market


class BtceUSD(Market):
    def __init__(self):
        super(BtceUSD, self).__init__("USD")
        # bitcoin central maximum call / day = 5000
        # keep 2500 for other operations
        self.update_rate = 60
        # {withdraw: amount bitcoins charged as network fee, exchange_rate: % for currency exchange}
        self.fees = {'withdraw': 0.1, 'exchange_rate': 0.002}

    def update_depth(self):
        try:
            res = urllib2.urlopen('https://btc-e.com/api/2/btc_usd/depth')
            depth = json.loads(res.read())
            self.depth = self.format_depth(depth)
        except:
            self.depth = {'asks': [], 'bids': []}
            logging.error("BtceUSD - depth data fetch error.")

    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i[0]), 'amount': float(i[1])})
        return r

    def format_depth(self, depth):
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = BtceUSD()
    print market.get_ticker()

import requests
import json
import logging
from market import Market

class BitfloorUSD(Market):
    def __init__(self):
        super(BitfloorUSD, self).__init__("USD")
        # {withdraw: amount bitcoins charged as network fee, exchange_rate: % for currency exchange}
        self.fees = {'withdraw': 0, 'exchange_rate': 0.004}

    def update_depth(self):
        try:
            response = requests.get('https://api.bitfloor.com/book/L2/1', timeout=self.request_timeout)
            depth = json.loads(response.text)
            self.depth = self.format_depth(depth)
        except requests.exceptions.Timeout:
            self.depth = {'asks': [], 'bids': []}
            logging.error("BitfloorUSD - request timed out.")
        except Exception, e:
            print e
            self.depth = {'asks': [], 'bids': []}
            logging.error("BitfloorUSD - depth data fetch error.")

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
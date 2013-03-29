import urllib2
import json
import logging
from market import Market


class MtGoxEUR(Market):
    def __init__(self):
        super(MtGoxEUR, self).__init__("EUR")
        self.update_rate = 25
        self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [{'price': 0, 'amount': 0}]}

    def update_depth(self):
        res = urllib2.urlopen('http://data.mtgox.com/api/1/BTCEUR/depth/fetch')
        jsonstr = res.read()
        try:
            data = json.loads(jsonstr)
        except Exception:
            logging.error("%s - Can't parse json: %s" % (self.name, jsonstr))
        if data["result"] == "success":
            self.depth = self.format_depth(data["return"])
        else:
            logging.error("%s - fetched data error" % (self.name))

    def sort_and_format(self, l, reverse=False):
        # sort list: for each dict in input list, get price key and sort by that
        l.sort(key=lambda x: float(x.get('price')), reverse=reverse)
        ret = []
        for i in l:
            # create a return a list of dicts sorted according to bid/ask w/ only the price and volume
            ret.append({'price': float(i['price']), 'amount': float(i['amount'])})
        return ret

    def format_depth(self, depth):
        # returns a dict for comparison against other exchanges in arbitrage.py:tick()
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = MtGoxEUR()
    print market.get_depth()

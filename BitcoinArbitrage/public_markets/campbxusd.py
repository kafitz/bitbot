import urllib2
import json
import logging
from market import Market

class CampBXUSD(Market):
    '''Updates CampBX depth tables'''
    def __init__(self):
        super(CampBXUSD, self).__init__("USD")
        self.update_rate = 25
        self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [{'price': 0, 'amount': 0}]}
        # {withdraw: amount bitcoins charged as network fee, exchange_rate: % for currency exchange}
        self.fees = {'withdraw': 0, 'exchange_rate': 0.0055}


    def update_depth(self):
        try:
            res = urllib2.urlopen('http://campbx.com/api/xdepth.php')
            jsonstr = res.read()
            data = json.loads(jsonstr)
            self.depth = self.format_depth(data)
        except:
            logging.error("%s - depth data fetch error." % (self.name,))

    def sort_and_format(self, l, reverse=False):
        # Sort the list of prices/amount lists by price
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        # Create a dict pair from each list keypair
        ret = []
        for i in l:
            ret.append({'price': float(i[0]), 'amount': float(i[1])})
        return ret

    def format_depth(self, data):
        bids = self.sort_and_format(data["Bids"], True)
        asks = self.sort_and_format(data["Asks"], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = CampBXUSD()
    print market.get_depth()

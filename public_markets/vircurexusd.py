import requests
import json
import logging
from market import Market

class VircurexUSD(Market):
    '''Updates CampBX depth tables'''
    def __init__(self):
        super(VircurexUSD, self).__init__("USD")
        self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [{'price': 0, 'amount': 0}]}
        # {withdraw: amount bitcoins charged as network fee, exchange_rate: % for currency exchange}
        self.fees = {'withdraw': 0.01, 'exchange_rate': 0.005} # 5%

    def update_depth(self):
        try:
            response = requests.get('https://vircurex.com/api/orderbook.json?base=BTC&alt=USD', timeout=self.request_timeout)
            data = json.loads(response.text)
            self.depth = self.format_depth(data)
        except requests.exceptions.Timeout:
            self.depth = {'asks': [], 'bids': []}
            logging.error("VircurexUSD - request timed out.")
        except:
            self.depth = {'asks': [], 'bids': []}
            logging.error("VircurexUSD - depth data fetch error.")

    def sort_and_format(self, l, reverse=False):
        # Sort the list of prices/amount lists by price
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        # Create a dict pair from each list keypair
        ret = []
        for i in l:
            ret.append({'price': float(i[0]), 'amount': float(i[1])})
        return ret

    def format_depth(self, data):
        bids = self.sort_and_format(data["bids"], True)
        asks = self.sort_and_format(data["asks"], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = VircurexUSD()
    print market.get_depth()

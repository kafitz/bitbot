import requests
import json
from market import Market


class Bitcoin24USD(Market):
    def __init__(self):
        super(Bitcoin24USD, self).__init__("USD")
        # {withdraw: amount bitcoins charged as network fee, exchange_rate: % for currency exchange}
        self.fees = {'withdraw': 0, 'exchange_rate': 0}

    def update_depth(self):
        try:
            response = requests.get('https://bitcoin-24.com/api/USD/orderbook.json', timeout=config.request_timeout)
            depth = json.loads(response.text)
            self.depth = self.format_depth(data)
        except requests.exceptions.Timeout:
            self.depth = {'asks': [], 'bids': []}
            logging.error("Bitcoin24USD - request timed out.")
        except:
            self.depth = {'asks': [], 'bids': []}
            logging.error("Bitcoin24USD - depth data fetch error.")

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
    market = Bitcoin24USD()
    print json.dumps(market.get_ticker())

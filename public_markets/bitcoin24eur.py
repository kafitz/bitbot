import requests
import json
from market import Market


class Bitcoin24EUR(Market):
    def __init__(self):
        super(Bitcoin24EUR, self).__init__("EUR")
        self.update_rate = 20

    def update_depth(self):
        try:
            response = requests.get('https://bitcoin-24.com/api/EUR/orderbook.json', timeout=config.request_timeout)
            depth = json.loads(response.text)
            self.depth = self.format_depth(depth)
        except requests.exceptions.Timeout:
            self.depth = {'asks': [], 'bids': []}
            logging.error("Bitcoin24EUR - request timed out.")
        except:
            self.depth = {'asks': [], 'bids': []}
            logging.error("Bitcoin24EUR - depth data fetch error.")

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
    market = Bitcoin24EUR()
    print json.dumps(market.get_ticker())

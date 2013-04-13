import requests
import json
from market import Market


class BitcoinCentralEUR(Market):
    def __init__(self):
        super(BitcoinCentralEUR, self).__init__("EUR")
        # bitcoin central maximum call / day = 5000
        # keep 2500 for other operations
        self.update_rate = 24 * 60 * 60 / 2500

    def update_depth(self):
        try:
            response = requests.get('https://bitcoin-central.net/api/v1/depth?currency=EUR', timeout=config.request_timeout)
            depth = json.loads(response.text)
            self.depth = self.format_depth(data)
        except requests.exceptions.Timeout:
            self.depth = {'asks': [], 'bids': []}
            logging.error("BitcoinCentralEUR - request timed out.")
        except:
            self.depth = {'asks': [], 'bids': []}
            logging.error("BitcoinCentralEUR - depth data fetch error.")

    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: float(x['price']), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i['price']), 'amount': float(i['amount'])})
        return r

    def format_depth(self, depth):
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = BitcoinCentralEUR()
    print market.get_ticker()

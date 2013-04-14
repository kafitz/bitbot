from market import Market
import time
import datetime
import base64
import hmac
import hashlib
import urllib
import sys
import json
import re
import requests
from decimal import Decimal

class PrivateBitfloor(Market):
    name = 'Bitfloor'
    trade_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/order/new'}
    open_orders_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/orders'}
    info_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/accounts'}
    withdraw_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/withdraw'}
    cancel_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/order/cancel'}

    def __init__(self):
        super(Market, self).__init__()
        self.key = self.config.bitfloor_key
        self.secret = self.config.bitfloor_secret
        self.passphrase = self.config.bitfloor_passphrase
        self.currency = 'USD'
        self.error = ''
        self.last_opportunity = None

    def _create_nonce(self):
        return int(time.time() * 1000000)

    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, url, params, extra_headers=None):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'bitfloor-key': self.key,
            'bitfloor-sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), urllib.urlencode(params), hashlib.sha512).digest())),
            'bitfloor-passphrase':  self.passphrase,
            'bitfloor-version': 1,
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        try:
            response = requests.post(url['url'], data=params, headers=headers, timeout=5)
        except requests.exceptions.Timeout:
            print "Request timed out."
            self.error = "request timed out"
            return
        except requests.exceptions.SSLError, e:
            print e
            print "SSL Error: check server certificate to " + self.name
            self.error = str(e)
            return
        if response.status_code == 200:
            jsonstr = json.loads(response.text)
            return jsonstr
        elif response.status_code == 502:
            print "Bitfloor 502"
            self.error = "bitfloor: 502"
            return
        return 0

    def trade(self, product_id, amount, side, price=None):
        params = [('nonce', self._create_nonce()),
                  ('product_id', product_id),
                  ('size', str(amount)),
                  ('side', side)]
        if price:
            params.append(('price', str(price)))
        response = self._send_request(self.trade_url, params)
        if response and 'error' not in response:
            self.price = str(price)
            self.id = str(response['order_id'])
            self.timestamp = self._format_time(response['timestamp'])
            self.amount = str(amount)
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def buy(self, amount, price):
        product_id = 1  # indicates exchanges as BTCUSD
        side = 0 # indicates buy order
        return self.trade(product_id, amount, side, price)

    def sell(self, amount, price):
        product_id = 1
        side = 1 # indicates sell order
        return self.trade(product_id, amount, side, price)

    def get_info(self):
        params = [('nonce', self._create_nonce())]
        response = self._send_request(self.info_url, params)
        if response and 'error' not in response:
            for wallet in response:
                if str(wallet['currency']) == 'BTC':
                    self.btc_balance = float(wallet['amount'])
                elif str(wallet['currency']) == 'USD':
                    self.usd_balance = float(wallet['amount'])
                self.fee = 0.10
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        self.btc_balance = None
        self.usd_balance = None
        return 0

    def get_txs(self):
        self.error = 'this API can\'t list transactions'
        return 1
        
    def get_orders(self):
        params = [('nonce', self._create_nonce())]
        response = self._send_request(self.open_orders_url, params)
        self.orders_list = []
        if len(response) == 0:
            self.error = 'no open orders listed'
            return 1
        elif response and 'error' not in response:
            for order in response:
                o = {}
                if order['side'] == 0:
                    o['type'] = 'buy'
                elif order['side'] == 1:
                    o['type'] = 'sell'
                o['timestamp'] = self._format_time(order['timestamp'])
                o['price'] = unicode(round(float(order['price']), 2)) + ' USD/BTC' # Round to 2 places (e.g., $5.35) and output a unicode
                o['amount'] = unicode(round(float(order['size']), 4)) + ' BTC' # e.g., 3.2534 BTC
                o['id'] = order['order_id']
                self.orders_list.append(o)
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def cancel(self, order_id):
        self.get_orders()
        if len(self.orders_list) == 0:
            self.error = 'no open orders listed'
            return 1
        for order in self.orders_list:
            if order_id == order['id']:
                order_amount = order['amount']
                self.cancelled_amount = order_amount
                
        params = [('nonce', self._create_nonce()),('order_id', order_id),('product_id', '1')]
        response = self._send_request(self.cancel_url, params)
        if response and 'error' not in response:
            self.cancelled_id = response['order_id']
            self.cancelled_time = self._format_time(response['timestamp'])
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def withdraw(self, amount, destination):
        params = [('nonce', self._create_nonce()),
                  ('currency', 'BTC'),
                  ('method', 'bitcoin'),
                  ('amount', amount),
                  ('destination', destination)]
        response = self._send_request(self.withdraw_url, params)
        if response and 'error' not in response:
            self.timestamp = self._format_time(response['timestamp'])
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def deposit(self):
        # hardcoded bitcoin address, because there's no way to get it from the API
        self.address = '1FbvTUCsuVi1cpYwX5TnNQyUQqb3LZo4xg'
        return 1

    def get_lag(self):
        self.error = 'not available from this API'
        return 1
        
if __name__ == '__main__':
    bitfloor = PrivateBitfloor()
    bitfloor.get_info()
    print bitfloor.btc_balance

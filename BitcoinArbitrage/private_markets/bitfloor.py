from market import Market
import time
import datetime
import base64
import hmac
import urllib
import urllib2
import hashlib
import sys
import json
import re
from decimal import Decimal


class PrivateBitfloor(Market):
    name = 'Bitfloor'
    ticker_url = {'method': 'GET', 'url': ''}
    trade_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/order/new'}
    order_url = {'method': 'POST', 'url': 'https://api.bitfloor.com/order/details'}
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

    def _create_nonce(self):
        return int(time.time() * 1000000)

    def _change_currency_url(self, url, currency):
        return re.sub(r'BTC\w{3}', r'BTC' + currency, url)

    def _to_int_price(self, price, currency):
        ret_price = None
        if currency in ['USD', 'EUR', 'GBP', 'PLN', 'CAD', 'AUD', 'CHF', 'CNY',
                        'NZD', 'RUB', 'DKK', 'HKD', 'SGD', 'THB']:
            ret_price = Decimal(price)
            ret_price = int(price * 100000)
        elif currency in ['JPY', 'SEK']:
            ret_price = Decimal(price)
            ret_price = int(price * 1000)
        return ret_price

    def _to_int_amount(self, amount):
        amount = Decimal(amount)
        return int(amount * 100000000)

    def _from_int_amount(self, amount):
        return Decimal(amount) / Decimal(100000000.)

    def _from_int_price(self, amount):
        return Decimal(amount) / Decimal(100000.)
        
    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, url, params, extra_headers=None):
        enc_params = urllib.urlencode(params)
        headers = {
            'bitfloor-key': self.key,
            'bitfloor-sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), enc_params, hashlib.sha512).digest())),
            'bitfloor-passphrase':  self.passphrase,
            'bitfloor-version': 1,
            'Content-type': 'application/x-www-form-urlencoded',
        }

        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        req = urllib2.Request(url['url'], enc_params, headers)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            print str(e)
            return json.loads(e.read())
        else:
            jsonstr = json.loads(response.read())
            return jsonstr
        return None

    def trade(self, product_id, size, side, price=None):
        params = [('nonce', self._create_nonce()),
                  ('product_id', product_id),
                  ('size', str(size)),
                  ('side', side)]

        if price:
            params.append(('price', str(price)))
        response = self._send_request(self.trade_url, params)
        print response
        if response and 'error' not in response:
            self.price = str(price)
            self.id = str(response['order_id'])
            self.timestamp = self._format_time(response['timestamp'])
            self.amount = str(size)
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return None

    def buy(self, amount, price):
        product_id = 1  # indicates exchanges as BTCUSD
        side = 0 # indicates buy order
        size = amount
        return self.trade(product_id, size, side, price)

    def sell(self, amount, price):
        product_id = 1
        side = 1 # indicates sell order
        size = amount
        return self.trade(product_id, size, side, price)

    def get_info(self):
        params = [('nonce', self._create_nonce())]
        response = self._send_request(self.info_url, params)
        if response and 'error' not in response:
            for wallet in response:
                if str(wallet['currency']) == 'BTC':
                    self.btc_balance = float(wallet['amount'])
                elif str(wallet['currency']) == 'USD':
                    self.usd_balance = float(wallet['amount'])
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return None

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
            return
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return None
        
    def cancel(self, order_id):
        self.get_orders()
        params = [('nonce', self._create_nonce()),('order_id', order_id),('product_id', '1')] # product_id = 1 => BTC/USD exchange      
        response = self._send_request(self.cancel_url, params)
        
        for order in self.orders_list:
            if order_id == order['id']:
                order_amount = order['amount']
        if response and 'error' not in response:
            self.cancelled_id = response['order_id']
            self.cancelled_time = self._format_time(response['timestamp'])
            self.cancelled_amount = order_amount
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
            
    def deposit(self):
        # hardcoded bitcoin address, because there's no way to get it from the API
        self.address = "1FbvTUCsuVi1cpYwX5TnNQyUQqb3LZo4xg"
        return 1

    def withdraw(self, amount, destination):
        params = [('nonce', self._create_nonce()),('currency', 'BTC'), ('method', 'bitcoin'), ('amount', amount), ('destination', destination)]
        response = self._send_request(self.withdraw_url, params)
        
        if response and 'error' not in response:
            self.timestamp = self._format_time(response['timestamp'])
            print response
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return None


if __name__ == '__main__':
    bitfloor = PrivateBitfloor()
    bitfloor.get_info()

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

class PrivateMtGox(Market):
    name = 'MtGox'
    trade_url = 'https://data.mtgox.com/api/1/BTCUSD/private/order/add'
    open_orders_url = 'https://mtgox.com/api/1/generic/private/orders'
    info_url = 'https://mtgox.com/api/1/generic/private/info'
    tx_url = 'https://data.mtgox.com/api/1/generic/private/wallet/history'
    withdraw_url = 'https://data.mtgox.com/api/1/generic/bitcoin/send_simple'
    cancel_url = 'https://data.mtgox.com/api/0/cancelOrder.php'
    deposit_url = 'https://data.mtgox.com/api/1/generic/bitcoin/address'
    lag_url = 'https://data.mtgox.com/api/1/generic/order/lag'

    def __init__(self):
        super(Market, self).__init__()
        self.key = self.config.mtgox_key
        self.secret = self.config.mtgox_secret
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
            ret_price = int(ret_price * 100000)
        elif currency in ['JPY', 'SEK']:
            ret_price = Decimal(price)
            ret_price = int(ret_price * 1000)
        return ret_price

    def _to_int_amount(self, amount):
        amount = Decimal(amount) * 100000000
        return int(amount)

    def _from_int_amount(self, amount):
        return Decimal(amount) / Decimal(100000000.)

    def _from_int_price(self, amount):
        return Decimal(amount) / Decimal(100000.)
        
    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, url, params, extra_headers=None):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Rest-Key': self.key,
            'Rest-Sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), urllib.urlencode(params), hashlib.sha512).digest())),
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v
        req = urllib2.Request(url, urllib.urlencode(params), headers)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            return {'error': str(e)}
        else:
            jsonstr = json.loads(response.read())
            return jsonstr
        return 0

    def trade(self, amount, ttype, price=None):
        if price:
            int_price = self._to_int_price(price, self.currency)
        int_amount = self._to_int_amount(amount)
        
        self.buy_url = self._change_currency_url(self.trade_url, self.currency)

        params = [('nonce', self._create_nonce()),
                  ('amount_int', str(int_amount)),
                  ('type', ttype)]
        if price:
            params.append(('price_int', str(int_price)))

        response = self._send_request(self.buy_url, params)
        if response and 'error' not in response:
            self.price = str(price)
            self.id = str(response['return'])
            self.timestamp = str(datetime.datetime.now())
            self.amount = amount
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def buy(self, amount, price):
        return self.trade(amount, 'bid', price)

    def sell(self, amount, price=None):
        return self.trade(amount, 'ask', price)

    def get_info(self):
        params = [('nonce', self._create_nonce())]
        response = self._send_request(self.info_url, params)
        if response and 'result' in response and response['result'] == 'success':
            self.btc_balance = self._from_int_amount(int(response['return']['Wallets']['BTC']['Balance']['value_int']))
            self.usd_balance = self._from_int_price(int(response['return']['Wallets']['USD']['Balance']['value_int']))
            self.fee = float(response['return']['Trade_Fee'])
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def get_txs(self):
        params = [('nonce', self._create_nonce()),('currency', self.currency)]
        response = self._send_request(self.tx_url, params)
        self.tx_list = []
        if response['result'] == 'success':
            for transaction in response['return']['result']:
                tx = {}
                tx['type'] = transaction['Type']
                tx['timestamp'] = self._format_time(transaction['Date'])
                tx['desc'] = transaction['Info'].encode('utf-8')
                self.tx_list.append(tx)
            if len(self.tx_list) == 0:
                self.error = 'no recent transactions found'
            return 1
        return 0

    def get_orders(self):
        params = [('nonce', self._create_nonce())]
        response = self._send_request(self.open_orders_url, params)
        self.orders_list = []
        if response and 'error' not in response and len(response['return']) == 0:
            self.error = 'no open orders listed'
            return 1
        elif response and 'error' not in response:
            for order in response['return']:
                o = {}
                if order['type'] == 'ask':
                    o['type'] = 'sell'
                if order['type'] == 'bid':
                    o['type'] = 'buy'
                o['timestamp'] = self._format_time(order['date'])
                o['price'] = order['price']['display_short']
                o['amount'] = order['amount']['display_short']
                o['id'] = order['oid']
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
                order_type = order['type']
                self.cancelled_amount = order['amount']
        try:
            order_type = order_type
        except:
            self.error = 'order does not exist'
            return 1

        params = [('nonce', self._create_nonce()),
                  ('oid', order_id),
                  ('type', order_type)]
        response = self._send_request(self.cancel_url, params)
        if response and 'error' not in response:
            self.cancelled_id = order_id
            self.cancelled_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def withdraw(self, amount, destination, fee=None):
        params = [('nonce', self._create_nonce()),
                  ('amount_int', self._to_int_amount(amount)),
                  ('address', str(destination))]
        if fee:
            params += ('fee', fee)
        response = self._send_request(self.withdraw_url, params)
        if response and 'error' not in response:
            self.timestamp = str(datetime.datetime.now()).split('.')[0]
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def deposit(self):
        params = [('nonce', self._create_nonce())]
        response = self._send_request(self.deposit_url, params)
        if response and 'error' not in response:
            self.address = response['return']['addr']
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def get_lag(self):
        params = []
        response = self._send_request(self.lag_url, params)
        if response and 'error' not in response:
            self.lag = response['return']['lag_text']
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0
        
if __name__ == '__main__':
    mtgox = PrivateMtGox()

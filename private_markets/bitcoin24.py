from market import Market
import time
import datetime
import base64
import hmac
import hashlib
import sys
import json
import re
import requests
from decimal import Decimal


class PrivateBitcoin24(Market):
    name = "Bitcoin24"
    url = "https://bitcoin-24.com/api/user_api.php"

    def __init__(self):
        super(Market, self).__init__()
        self.user = self.config.bitcoin24_user
        self.key = self.config.bitcoin24_key
        self.currency = "USD"
        self.initials = "bc24"
        self.error = ""
        self.last_opportunity = None

    def _create_nonce(self):
        return int(time.time())

    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, params, extra_headers=None):
        params.update({'user': self.user, 'key': self.key})
        headers = {
            'Content-type': 'application/x-www-form-urlencoded'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        try:
            # print "request to bitcoin24: " + str(params) # request debug
            response = requests.post(self.url, data=params, headers=headers, timeout=self.config.request_timeout)
        except requests.exceptions.Timeout:
            print "Request timed out."
            self.error = "request timed out"
            return
        except requests.exceptions.SSLError, e:
            print e
            print "SSL Error: check server certificate to " + self.name
            self.error = "SSL certificate mismatch"
            return
        if response.status_code == 200:
            try:
                return json.loads(response.text)
            except Exception, e:
                print e
                return None
        return None

    def trade(self, params):
        response = self._send_request(params)
        if response and 'error' not in response:
            self.id = response['id']
            self.timestamp = self._format_time(reponse['date'])
            self.amount = response['amount']
            return 1
        elif 'error' in response:
            self.error = str(response['message'])
            return 1
        return 0

    def buy(self, amount, price):
        params = {'api': 'buy_btc', "amount": str(amount), "price": str(price), "cur": "USD"}
        return self.trade(params)

    def sell(self, amount, price):
        params = {'api': 'sell_btc', "amount": str(amount), "price": str(price), "cur": "USD"}
        return self.trade(params)

    def cancel(self, order_id):
        params = {"api": "cancel_order", "id": order_id}
        response = self._send_request(params)
        if response and 'True' in response:
            self.cancelled_id = order_id
            self.cancelled_time = self._format_time(time.time())
            return 1
        elif response and 'error' in response:
            self.error = str(response['message'])
            return 1
        return 0 

    def get_info(self):
        params = {"api": "get_balance"}
        response = self._send_request(params)
        if response and 'error' not in response:
            self.btc_balance = float(response['btc_available'])
            self.usd_balance = float(response['usd'])
            self.fee = 0
            return 1
        self.btc_balance = None
        self.usd_balance = None
        return 0

    def get_orders(self):
        params = {"api": "open_orders"}
        response = self._send_request(params)
        self.orders_list = []
        if response and 'error' not in response:
            for order in response:
                o = {}
                if order['type'] == 1:
                    o['type'] = 'buy'
                elif order['type'] == 2:
                    o['type'] = 'sell'
                o['timestamp'] = self._format_time(order['date'])
                o['price'] = order['price']
                o['amount'] = order['amount']
                o['id'] = order['id']
                self.orders_list.append(o)
            return 1
        elif response and 'error' in response:
            self.error = str(response['message'])
            return 1
        return None
        
    def withdraw(self, amount, destination):
        params = {"api": "withdraw_btc", "amount": amount, "address": destination}
        response = self._send_request(params)
        if response and 'trans' in response:
            self.timestamp = self._format_time(time.time())
            return 1
        elif response and 'error' in response:
            self.error = response['message']
            return 1
        return None

    def get_txs(self):
        params = {'api': 'trades_json'}
        response = self._send_request(params)
        self.tx_list = []
        for trans in response:
            tx = {}
            tx['type'] = trans[u'type']
            tx['timestamp'] = self._format_time(trans[u'date'])
            if tx['type'] == 'buy':
                ttype = 'bought'
            elif tx['type'] == 'sell':
                ttype = 'sold'
            tx_description = "BTC " + ttype + ": [tid:" + str(trans[u'tid']) + "] " + str(trans[u'amount']) +\
                " BTC at $" + str(trans['price'])
            tx['desc'] = tx_description
            self.tx_list.append(tx)
        if len(self.tx_list) == 0:
            self.error = 'no recent transactions found'
            return 1
        return 0

    def deposit(self):
        params = {"api": "get_addr"}
        response = self._send_request(params)
        if response and 'address' in response:
            self.address = response['address']
            return 1
        return 0
        
    def get_lag(self):
        self.error = 'not available from this API'
        return 1

    def __str__(self):
        return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance})


if __name__ == "__main__":
    bitcoin24 = PrivateBitcoin24()
    bitcoin24.get_info()
    print bitcoin24.btc_balance
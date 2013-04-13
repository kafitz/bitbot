from market import Market
import time
import datetime
import base64
import hmac
import urllib
import urllib2
import httplib
import hashlib
import sys
import json
import re
import requests
from decimal import Decimal


class PrivateBTCe(Market):
    name = "BTC-e"
    url = "https://btc-e.com/tapi"

    def __init__(self):
        super(Market, self).__init__()
        self.key = self.config.btce_key
        self.secret = self.config.btce_secret
        self.currency = "USD"
        self.initials = "btce"
        self.error = ""
        self.last_opportunity = None

    def _create_nonce(self):
        return int(time.time())

    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, params, extra_headers=None):
        params["nonce"] = self._create_nonce()
        ahmac = hmac.new(self.secret, digestmod=hashlib.sha512)
        ahmac.update(urllib.urlencode(params))
        sign = ahmac.hexdigest()
        headers = {
            'Key': self.key,
            'Sign': sign,
            'Content-type': 'application/x-www-form-urlencoded'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        try:
            response = requests.post(self.url, data=params, headers=headers, timeout=5)
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

    def trade(self, amount, ttype, price):
        params = {"method": "Trade", "amount": amount, "type": ttype, "rate": price, "pair": "btc_usd"}
        response = self._send_request(params)
        if response and response["success"] == 1:
            ret = response["return"]
            for key in ret.keys():
                self.id = key
                self.timestamp = self._format_time(key['timestamp'])
                self.amount = key['amount']
                return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def buy(self, amount, price):
        return self.trade(amount, "buy", price)

    def sell(self, amount, price):
        return self.trade(amount, "sell", price)

    def cancel(self, order_id):
        params = {"method": "CancelOrder"}
        response = self._send_request(params)
        if response and 'error' not in response:
            self.cancelled_id = response['order_id']
            self.cancelled_time = self._format_time(time.time())
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0 

    def get_info(self):
        params = {"method": "getInfo"}
        response = self._send_request(params)
        if response and 'error' not in response:
            funds = response['return']['funds']
            self.btc_balance = float(funds['btc'])
            self.usd_balance = float(funds['usd'])
            try: # try to set fee dynamically from API
                fee_res = requests.get('https://btc-e.com/api/2/btc_usd/fee')
                fee_json = json.loads(fee_res.text)
                self.fee = float(fee_json['trade'])
            except: # otherwise pass last known fee
                self.fee = 0.2
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        self.btc_balance = None
        self.usd_balance = None
        self.error = str(response)
        return None

    def get_orders(self, from_id=None, end_id=None):
        params = {"method": "OrderList"}
        if from_id:
            params["from_id"] = from_id
        if end_id:
            params["end_id"]
        response = self._send_request(params)
        self.orders_list = []
        if response and 'error' not in response:
            print response
            return 1
        elif response and 'error' in response:
            self.error = 'no open orders listed'
            return 1
        return None
        
    def withdraw(self, amount, destination):
        params = [("currency", "BTC"), ("method", "bitcoin"), ("amount", amount), ("destination", destination)]
        response = self._send_request(params)
        if response:
            print response
            return 1
        return None

    def get_txs(self):
        self.error = 'txs for this API has not yet been implemented'
        return 1
        
    def get_lag(self):
        self.error = 'not available from this API'
        return 1

    def deposit(self):
        self.address = '1Knte8LA9RFEFVMfrk46SPgjN5gt562nWc'
        return 1

    def __str__(self):
        return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance})


if __name__ == "__main__":
    btce = PrivateBTCe()
    btce.get_info()
    print btce.usd_balance
    #bitfloor.withdraw(0,"1E774iqGeTrr7GUP1L6jpwDsWg1pERQhNo")
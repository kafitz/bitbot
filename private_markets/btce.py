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
from decimal import Decimal


class PrivateBTCe(Market):
    url_base = "btc-e.com"
    url_suffix = "/tapi"

    def __init__(self):
        super(Market, self).__init__()
        self.key = self.config.btce_key
        self.secret = self.config.btce_secret
        self.currency = "USD"
        self.initials = "btce"
        self.error = ""
        #self.get_info()

    def _create_nonce(self):
        return int(time.time())

    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, params, extra_headers=None):
        params["nonce"] = self._create_nonce()
        encoded_params = urllib.urlencode(params)
        ahmac = hmac.new(self.secret, digestmod=hashlib.sha512)
        ahmac.update(encoded_params)
        sign = ahmac.hexdigest()
        headers = {
            'Key': self.key,
            'Sign': sign,
            'Content-type': 'application/x-www-form-urlencoded'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        conn = httplib.HTTPSConnection(self.url_base)
        conn.request("POST", self.url_suffix, encoded_params, headers)
        response = conn.getresponse()
        if response.status == 200:
            jsonstr = response.read()
            conn.close()
            return json.loads(jsonstr)
        conn.close()
        return None

    def trade(self, amount, ttype, price):
        params = {"method": "Trade", "amount": amount, "type": ttype, "rate": price, "pair": "btc_usd"}
        response = self._send_request(params)
        print response
        if response and response["success"] == 1:
            ret = response["return"]
            for key in ret.keys():
                self.id = key
                self.timestamp = self._format_time(key['timestamp'])
                self.amount = key['amount']
                return 1
        elif 'error' in response:
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
            fee_res = urllib2.urlopen('https://btc-e.com/api/2/btc_usd/fee')
            fee_json = json.loads(fee_res.read())
            self.fee = float(fee_json['trade'])
            return 1
        elif 'error' in response:
            self.error = str(response['error'])
            return 1
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
        elif 'error' in response:
            self.error = str(response['error'])
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
        

    def __str__(self):
        return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance})


if __name__ == "__main__":
    btce = PrivateBTCe()
    btce.get_info()
    # print btce
    #bitfloor.withdraw(0,"1E774iqGeTrr7GUP1L6jpwDsWg1pERQhNo")
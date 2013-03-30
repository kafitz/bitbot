from market import Market
import time
import base64
import hmac
import urllib
import urllib2
import hashlib
import sys
import json
import re
from decimal import Decimal


class PrivateBTCe(Market):
    ticker_url = {"method": "GET", "url": ""}
    buy_url = {"method": "POST", "url": ""}
    sell_url = {"method": "POST", "url": ""}
    order_url = {"method": "POST", "url": ""}
    open_orders_url = {"method": "POST", "url": ""}
    info_url = {"method": "POST", "url": "https://btc-e.com/tapi/getInfo"}
    withdraw_url = {"method": "POST", "url": ""}

    def __init__(self):
        super(Market, self).__init__()
        self.key = self.config.btce_key
        self.secret = self.config.btce_secret
        self.passphrase = self.config.btce_passphrase
        self.currency = "USD"
        self.initials = "btce"
        #self.get_info()

    def _create_nonce(self):
        return int(time.time() * 1000000)

    def _change_currency_url(self, url, currency):
        return re.sub(r'BTC\w{3}', r'BTC' + currency, url)

    def _to_int_price(self, price, currency):
        ret_price = None
        if currency in ["USD", "EUR", "GBP", "PLN", "CAD", "AUD", "CHF", "CNY",
                        "NZD", "RUB", "DKK", "HKD", "SGD", "THB"]:
            ret_price = Decimal(price)
            ret_price = int(price * 100000)
        elif currency in ["JPY", "SEK"]:
            ret_price = Decimal(price)
            ret_price = int(price * 1000)
        return ret_price

    def _to_int_amount(self, amount):
        amount = Decimal(amount)
        return int(amount * 100000000)

    def _from_int_amount(self, amount):
        return Decimal(amount) / Decimal(100000000.)

    def _from_int_price(self, amount):
        # FIXME: should take JPY and SEK into account
        return Decimal(amount) / Decimal(100000.)

    def _send_request(self, url, params, extra_headers=None):
        headers = {
            'Key': self.key,
            'Sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), urllib.urlencode(params), hashlib.sha512).digest())),
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        req = urllib2.Request(url['url'], urllib.urlencode(params), headers)
        response = urllib2.urlopen(req)
        if response.getcode() == 200:
            jsonstr = response.read()
            return json.loads(jsonstr)
        return None

    def trade(self, amount, ttype, price=None):
        if price:
            price = self._to_int_price(price, self.currency)
        amount = self._to_int_amount(amount)

        self.buy_url["url"] = self._change_currency_url(self.buy_url["url"], self.currency)

        params = [("nonce", self._create_nonce()),
                  ("amount_int", str(amount)),
                  ("type", ttype)]
        if price:
            params.append(("price_int", str(price)))

        response = self._send_request(self.buy_url, params)
        if response and "result" in response and response["result"] == "success":
            return response["return"]
        return None

    def buy(self, amount, price=None):
        return self.trade(amount, "bid", price)

    def sell(self, amount, price=None):
        return self.trade(amount, "ask", price)

    def get_info(self):
        params = [("nonce", self._create_nonce())]
        response = self._send_request(self.info_url, params)
        if response:
            for wallet in response:
                if str(wallet['currency']) == 'BTC':
                    self.btc_balance = float(wallet['amount'])
                elif str(wallet['currency']) == 'USD':
                    self.usd_balance = float(wallet['amount'])
            return 1
        return None

    def get_orders(self):
        pass
        
    def withdraw(self, amount, destination):
        params = [("currency", "BTC"), ("method", "bitcoin"), ("amount", amount), ("destination", destination)]
        response = self._send_request(self.withdraw_url, params)
        if response:
            print response
            return 1
        return None
        

    def __str__(self):
        return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance})


if __name__ == "__main__":
    btce = PrivateBTCe()
    btce.get_info()
    print btce
    #bitfloor.withdraw(0,"1E774iqGeTrr7GUP1L6jpwDsWg1pERQhNo")
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
    ticker_url = "https://mtgox.com/api/1/BTCUSD/public/ticker"
    buy_url = "https://mtgox.com/api/1/BTCUSD/private/order/add"
    sell_url = "https://mtgox.com/api/1/BTCUSD/private/order/add"
    order_url = "https://mtgox.com/api/1/generic/private/order/result"
    open_orders_url = "https://mtgox.com/api/1/generic/private/orders"
    info_url = "https://mtgox.com/api/1/generic/private/info"
    cancel_url = "https://data.mtgox.com/api/0/cancelOrder.php"

    def __init__(self):
        super(Market, self).__init__()
        self.name = "MtGox"
        self.key = self.config.mtgox_key
        self.secret = self.config.mtgox_secret
        self.currency = "USD"
        self.initials = "mtgx"
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

    def _send_request(self, url, params=[], extra_headers=None):
        self.error = False
        params += [("nonce", self._create_nonce())]
        headers = {
            'Rest-Key': self.key,
            'Rest-Sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), urllib.urlencode(params), hashlib.sha512).digest())),
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        req = urllib2.Request(url, urllib.urlencode(params), headers)
        response = urllib2.urlopen(req)
        print response
        if response.getcode() == 200:
            jsonstr = response.read()
            return json.loads(jsonstr)
        return None

    def trade(self, amount, ttype, price=None):
        if price:
            price = self._to_int_price(price, self.currency)
        amount = self._to_int_amount(amount)

        self.buy_url = self._change_currency_url(self.buy_url, self.currency)

        params = [("amount_int", str(amount)),
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

    def cancel(self, order_id):
        params = [(u"oid", order_id)]
        self.get_orders()
        if len(self.orders_list) == 0:
            return "No open orders."
        for order in self.orders_list:
            if order_id == order["id"]:
                order_type = order["type"]
        print params, self.cancel_url

        pass

    def get_info(self):
        params = []
        response = self._send_request(self.info_url)
        if response and "result" in response and response["result"] == "success":
            self.btc_balance = self._from_int_amount(int(response["return"]["Wallets"]["BTC"]["Balance"]["value_int"]))
            self.usd_balance = self._from_int_price(int(response["return"]["Wallets"]["USD"]["Balance"]["value_int"]))
            self.fee = float(response["return"]["Trade_Fee"])
            return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance,"fee": self.fee})
        return None

    def get_orders(self):
        params = []
        response = self._send_request(self.open_orders_url)
        self.orders_list = []
        if response and "error" not in response:
            for order in response['return']:
                o = {}
                if order["type"] == "ask":
                    o["type"] = "sell"
                if order["type"] == "bid":
                    o["type"] = "buy"
                o["timestamp"] = datetime.datetime.fromtimestamp(int(order["date"])).strftime('%Y-%m-%d %H:%M:%S')
                o["price"] = order["price"]["display_short"]
                o["amount"] = order["amount"]["display_short"]
                o["id"] = order["oid"]
                self.orders_list.append(o)
            return 
        elif "error" in response:
            self.error = str(response["error"])
            self.orders_list = ['error']
            print self.error
            return 1

    def __str__(self):
        return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance,"fee": self.fee})


if __name__ == "__main__":
    mtgox = PrivateMtGox()
    mtgox.cancel("4439922a-2011-41ad-ad6e-59398b922d1b")
    # mtgox.get_orders()
    # print mtgox.orders_list
    #print mtgox

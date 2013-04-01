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
    name = "Bitfloor"
    ticker_url = {"method": "GET", "url": ""}
    buy_url = {"method": "POST", "url": "https://api.bitfloor.com/order/new"}
    sell_url = {"method": "POST", "url": "https://api.bitfloor.com/order/new"}
    order_url = {"method": "POST", "url": "https://api.bitfloor.com/order/details"}
    open_orders_url = {"method": "POST", "url": "https://api.bitfloor.com/orders"}
    info_url = {"method": "POST", "url": "https://api.bitfloor.com/accounts"}
    withdraw_url = {"method": "POST", "url": "https://testnet.bitfloor.com/withdraw"}
    cancel_url = {"method": "POST", "url": "https://api.bitfloor.com/order/cancel"}


    def __init__(self):
        super(Market, self).__init__()
        self.key = self.config.bitfloor_key
        self.secret = self.config.bitfloor_secret
        self.passphrase = self.config.bitfloor_passphrase
        self.currency = "USD"
        self.error = ""

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
        return Decimal(amount) / Decimal(100000.)

    def _send_request(self, url, params=[], extra_headers=None):
        params += [("nonce", self._create_nonce())]
        headers = {
            'bitfloor-key': self.key,
            'bitfloor-sign': base64.b64encode(str(hmac.new(base64.b64decode(self.secret), urllib.urlencode(params), hashlib.sha512).digest())),
            'bitfloor-passphrase':  self.passphrase,
            'bitfloor-version': 1,
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v

        req = urllib2.Request(url['url'], urllib.urlencode(params), headers)
        
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            print str(e)
            return json.loads(e.read())
        else:
            jsonstr = json.loads(response.read())
#            response.close()
            return jsonstr
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
        response = self._send_request(self.info_url)
        if response and "error" not in response:
            for wallet in response:
                if str(wallet['currency']) == 'BTC':
                    self.btc_balance = float(wallet['amount'])
                elif str(wallet['currency']) == 'USD':
                    self.usd_balance = float(wallet['amount'])
            return 1
        elif response and "error" in response:
            self.error = str(response["error"])
            return 1
        return None

    def get_txs(self, order_id):
        self.tx_list = []
        if order_id is None:
            return "Error: must enter an order ID for bitfloor."
        params = [("order_id", order_id)]
        transaction = self._send_request(self.order_url, params)
        if transaction:
            tx = {}
            if transaction['side'] == 0:
                tx['type'] = 'buy'
            elif transaction['side'] == 1:
                tx['type'] = 'sell'
            tx['timestamp'] = str(transaction["timestamp"])
            tx['id'] = transaction["order_id"]
            tx['usd'] = float(transaction["price"])
            tx['btc'] = float(transaction["size"])
            tx['fee'] = tx['usd'] * 0.001
            # tx['seq'] = float(transaction["fee"])
            self.tx_list.append(tx)
            return transaction
        return None
        
    def get_orders(self):
        response = self._send_request(self.open_orders_url)
        self.orders_list = []
        if response and "error" not in response:
            for order in response:
                o = {}
                if order['side'] == 0:
                    o['type'] = 'buy'
                elif order['side'] == 1:
                    o['type'] = 'sell'
                o['timestamp'] = datetime.datetime.fromtimestamp(float(order["timestamp"])).strftime('%Y-%m-%d %H:%M:%S')
                o['price'] = unicode(round(float(order["price"]), 2)) + " USD/BTC" # Round to 2 places (e.g., $5.35) and output a unicode
                o['amount'] = unicode(round(float(order["size"]), 4)) + " BTC" # e.g., 3.2534 BTC
                o['id'] = order['order_id']
                self.orders_list.append(o)
            return
        elif response and "error" in response:
            self.error = str(response["error"])
            return 1
        return None
        
    def cancel(self, order_id):
        params = [("order_id", order_id),("product_id", "1")]
        response = self._send_request(self.cancel_url, params)
        print response
        self.cancelled_id = response["order_id"]
        self.cancelled_time = datetime.datetime.fromtimestamp(float(response["timestamp"])).strftime('%Y-%m-%d %H:%M:%S')
        return 1
                

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
    bitfloor = PrivateBitfloor()
    bitfloor.get_orders()
    # print bitfloor
    #bitfloor.withdraw(0,"1E774iqGeTrr7GUP1L6jpwDsWg1pERQhNo")

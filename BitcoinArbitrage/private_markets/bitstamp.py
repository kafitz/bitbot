from market import Market
import datetime
import urllib
import urllib2
import sys
import json


class PrivateBitstamp(Market):
    name = "Bitstamp"
    ticker_url = {"method": "GET", "url": "https://www.bitstamp.net/api/ticker/"}
    buy_url = {"method": "POST", "url": "https://www.bitstamp.net/api/buy/"}
    sell_url = {"method": "POST", "url": "https://www.bitstamp.net/api/sell/"}
    tx_url = {"method": "POST", "url": "https://www.bitstamp.net/api/user_transactions/"}
    orders_url = {"method": "POST", "url": "https://www.bitstamp.net/api/open_orders/"}
    info_url = {"method": "POST", "url": "https://www.bitstamp.net/api/balance/"}
    cancel_url = {"method": "POST", "url": "https://bitstamp.net/api/cancel_order/"}

    def __init__(self):
        super(Market, self).__init__()
        self.user = self.config.bitstamp_user
        self.password = self.config.bitstamp_password
        self.currency = "USD"

    def _send_request(self, url, params, extra_headers=None):
        self.error = False
        headers = {
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
        except Exception, e:
            print e
            self.error = True
            self.errormsg = str(e)
            return None

        if response.getcode() == 200:
            jsonstr = response.read()
            return json.loads(jsonstr)
        return None

    def trade(self, amount, url, price):
        # Next line is commented out to avoid accidental trades, use with caution
        #params = {"user": self.user, "password": self.password, "amount": str(self.amount), "price": str(self.price)}
        response = self._send_request(self.url, params)
        print response
        if response and "result" in response and response["result"] == "success":
            return response["return"]
        return None

    def buy(self, amount, price):
        return self.trade(amount, buy_url, price)

    def sell(self, amount, price):
        return self.trade(amount, sell_url, price)

    def get_info(self):
        params = {"user": self.user, "password": self.password}
        response = self._send_request(self.info_url, params)

        if response and "error" not in response:
            self.usd_balance = float(response["usd_balance"])
            self.btc_balance = float(response["btc_balance"])
            self.usd_reserved = float(response["usd_reserved"])
            self.btc_reserved = float(response["btc_reserved"])
            self.usd_available = float(response["usd_available"])
            self.btc_available = float(response["btc_balance"])
            self.fee = float(response["fee"])
            return str({"btc_balance": self.btc_balance, "usd_balance": self.usd_balance})
            
        elif response and "error" in response:
            self.error = str(response["error"])
            print self.error
            return 1
        return None
        
    def get_txs(self, order_id=None):
        params = {"user": self.user, "password": self.password, "timedelta": "604800"}
        response = self._send_request(self.tx_url, params)
        self.tx_list = []
        if response:
            print response
            for transaction in response:
                tx = {}
                if transaction['type'] == 0:
                    tx['type'] = 'deposit'
                elif transaction['type'] == 1:
                    tx['type'] = 'withdrawal'
                elif transaction['type'] == 2:
                    if transaction['usd'] < 0:
                        tx['type'] = 'buy'
                    elif transaction['usd'] > 0:
                        tx['type'] = 'sell'
                tx['timestamp'] = str(transaction["datetime"])
                tx['id'] = str(transaction["id"])
                tx['usd'] = str(transaction["usd"])
                tx['btc'] = str(transaction["btc"])
                tx['fee'] = str(transaction["fee"])
                self.tx_list.append(tx)
            return response
        return None
    
    def get_orders(self):
        params = {"user": self.user, "password": self.password}
        response = self._send_request(self.orders_url, params)
        self.orders_list = []
        if response and "error" not in response:
            for order in response:
                o = {}
                if order['type'] == 0:
                    o['type'] = 'buy'
                elif order['type'] == 1:
                    o['type'] = 'sell'
                o['timestamp'] = str(order["datetime"])
                o['price'] = str(order["price"]) + " USD/BTC"
                o['amount'] = str(round(float(order["amount"]),1)) + " BTC"
                o['id'] = str(order['id'])
                self.orders_list.append(o)
            return 
        elif "error" in response:
            self.error = str(response["error"])
            print self.error
            return 1
        return None

    def cancel(self, order_id):
        params = {"user": self.user, "password": self.password}
        self.get_orders()
        if len(self.orders_list) == 0:
            return "No open orders."
        for order in self.orders_list:
            if order_id == order["id"]:
                order_type = order["type"]
        try:
            order_type = order_type
        except:
            return "Order does not exist."
        params = [(u"oid", order_id), (u"type", order_type)]
        response = self._send_request(self.cancel_url, params)
        print response
        self.cancelled_id = order_id
        self.cancelled_time = datetime.datetime.fromtimestamp(float(response["orders"][0]["date"])).strftime('%Y-%m-%d %H:%M:%S')
        return 1
        
if __name__ == "__main__":
    bitstamp = PrivateBitstamp()
    bitstamp.get_info()

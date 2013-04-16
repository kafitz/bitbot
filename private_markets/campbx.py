from market import Market
import time
import datetime
import sys
import json
import requests
from decimal import Decimal

class PrivateCampBX(Market):
    name = 'CampBX'
    trade_url = {'method': 'POST', 'url': 'https://campbx.com/api/tradeenter.php'}
    open_orders_url = {'method': 'POST', 'url': 'https://campbx.com/api/myorders.php'}
    tx_url = {'method': 'POST', 'url': 'https://campbx.com/api/user_transactions/'}
    info_url = {'method': 'POST', 'url': 'https://campbx.com/api/myfunds.php'}
    deposit_url = {'method': 'POST', 'url': 'https://campbx.com/api/getbtcaddr.php'}  
    withdraw_url = {'method': 'POST', 'url': 'https://campbx.com/api/sendbtc.php'}
    cancel_url = {'method': 'POST', 'url': 'https://campbx.com/api/tradecancel.php'}  

    def __init__(self):
        super(Market, self).__init__()
        self.user = self.config.campbx_user
        self.password = self.config.campbx_password
        self.currency = 'USD'
        self.error = ''
        self.last_opportunity = None
        
    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, url, params, extra_headers=None):
        params.update({'user': self.user, 'pass': self.password})
        try:
            response = requests.post(url['url'], data=params, timeout=config.request_timeout)
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
            try:
                jsonstr = json.loads(response.text)
                return jsonstr
            except Exception, e:
                print e
                return
        return 0

    def trade(self, amount, trademode, price):
        params = {'Quantity': amount,
                  'TradeMode' : str(trademode),
                  'Price': price}
        response = self._send_request(self.trade_url, params)
        print response
        if response and 'Success' in response:
            # Market order filled
            if response['Success'] == 0:
                self.price = price
                self.amount = amount
                self.id = 'successful market order'
                self.timestamp = self._format_time(time.time())
                return 1
            # Order not filled immediately
            else:
                self.price = price
                self.amount = amount
                self.id = response['Success']
                self.timestamp = self._format_time(time.time())
                return 1
        elif response and 'Error' in response:
            self.error = str(response['Error'])
            return 1
        return 0

    def buy(self, amount, price):
        return self.trade(amount, 'QuickBuy', price)

    def sell(self, amount, price):
        return self.trade(amount, 'QuickSell', price)

    def get_info(self):
        params = {}
        response = self._send_request(self.info_url, params)
        if response and 'Error' not in response:
            self.usd_balance = float(response['Total USD'])
            self.btc_balance = float(response['Total BTC'])
            self.fee = '0.55'
            return 1
        elif response and 'Error' in response:
            self.error = str(response['Error'])
            return 1
        self.btc_balance = None
        self.usd_balance = None
        return 0

    def get_txs(self):
        self.error = 'this API can\'t list transactions'
        return 1

    def get_orders(self):
        params = {}
        response = self._send_request(self.open_orders_url, params)
        self.orders_list = []

        if response and 'Info' in response['Sell'][0].keys() and 'Info' in response['Buy'][0].keys():
            self.error = 'no open orders listed'
            return 1
        if response and 'Info' not in response['Sell'][0].keys():
            for order in response['Sell']:
                o = {}
                o['type'] = 'Sell'
                o['timestamp'] = str(order['Order Entered'])
                o['price'] = str(order['Price']) + ' USD/BTC'
                o['amount'] = str(round(float(order['Quantity']),3)) + ' BTC'
                o['id'] = str(order['Order ID'])
                self.orders_list.append(o)
        if response and 'Info' not in response['Buy'][0].keys():  
             for order in response['Buy']:
                o = {}
                o['type'] = 'Buy'
                o['timestamp'] = str(order['Order Entered'])
                o['price'] = str(order['Price']) + ' USD/BTC'
                o['amount'] = str(round(float(order['Quantity']),3)) + ' BTC'
                o['id'] = str(order['Order ID'])
                self.orders_list.append(o)             
        if response and 'Error' in response:
            self.error = str(response['Error'])
            return 1
        return 0

    def cancel(self, order_id):
        self.get_orders()
        for order in self.orders_list:
            if order_id == order['id']:
                order_type = order['type']
                self.cancelled_amount = order['amount']
        try:
            order_type = order_type
        except:
            self.error = 'order does not exist'
            return 1

        params = {'OrderID': order_id,
                  'Type': order_type}
        response = self._send_request(self.cancel_url, params)
        
        if response:
            self.cancelled_id = order_id
            self.cancelled_time = str(datetime.datetime.now()).split('.')[0]
            return 1
        elif response:
            self.error = str(response['error'])
            return 1
        return 0

    def withdraw(self, amount, address):
        params = {'BTCAmt': str(amount), 
                  'BTCTo': str(address)}
        response = self._send_request(self.withdraw_url, params)
        if response and 'Error' not in response:
            self.timestamp = str(datetime.datetime.now())
            return 1
        elif response and 'Error' in response:
            self.error = str(response['Error'])
            return 1
        return 0

    def deposit(self):
        params = {}
        response = self._send_request(self.deposit_url, params)
        if response and 'Success' in response:
            self.address = response['Success']
            return 1
        elif response and 'Error' in response:
            self.error = str(response['Error'])
            return 1
        return 0

    def get_lag(self):
        self.error = 'not available from this API'
        return 1

if __name__ == '__main__':
    CampBX = PrivateCampBX()
    CampBX.get_info()
    print CampBX.usd_balance

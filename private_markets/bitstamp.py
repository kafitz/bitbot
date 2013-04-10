from market import Market
import datetime
import sys
import json
import requests

class PrivateBitstamp(Market):
    name = 'Bitstamp'
    buy_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/buy/'}
    sell_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/sell/'}
    open_orders_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/open_orders/'}
    tx_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/user_transactions/'}
    info_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/balance/'}
    deposit_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/bitcoin_deposit_address/'}  
    withdraw_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/bitcoin_withdrawal/'}
    cancel_url = {'method': 'POST', 'url': 'https://www.bitstamp.net/api/cancel_order/'}  

    def __init__(self):
        super(Market, self).__init__()
        self.user = self.config.bitstamp_user
        self.password = self.config.bitstamp_password
        self.currency = 'USD'
        self.error = ''
        self.last_opportunity = None

    def _format_time(self,timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def _send_request(self, url, params, extra_headers=None):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v
        try:
            response = requests.post(url['url'], data=params, headers=headers, timeout=3)
        except (requests.exceptions.Timeout, requests.exceptions.SSLError):
            print "Request timed out."
            self.error = "request timed out"
            return
        if response.status_code == 200:
            try:
                jsonstr = json.loads(response.text)
                return jsonstr
            except Exception, e:
                return e
        return 0

    def trade(self, url, amount, price):
        params = {'user': self.user, 'password': self.password, 'amount': str(amount), 'price': str(price)}
        response = self._send_request(url, params)
        if response and 'error' not in response:
            self.price = str(response['price'])
            self.id = str(response['id'])
            self.timestamp = str(response['datetime'])
            self.amount = str(response['amount'])
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def buy(self, amount, price):
        return self.trade(self.buy_url, amount, price)

    def sell(self, amount, price):
        return self.trade(self.sell_url, amount, price)

    def get_info(self):
        params = {'user': self.user, 'password': self.password}
        response = self._send_request(self.info_url, params)
        if response and 'error' not in response:
            self.usd_balance = float(response['usd_balance'])
            self.btc_balance = float(response['btc_balance'])
            self.fee = float(response['fee'])
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def get_txs(self):
        params = {'user': self.user, 'password': self.password, 'timedelta': '604800'}
        response = self._send_request(self.tx_url, params)
        self.tx_list = []
        if response:
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
                tx['timestamp'] = str(transaction['datetime'])
                tx['id'] = str(transaction['id'])
                tx['usd'] = str(transaction['usd'])
                tx['btc'] = str(round(float(transaction['btc']),3))
                tx['fee'] = str(transaction['fee'])
                tx['desc'] = '{0:10} | {1:6} USD | {2:6} BTC | fee {3:4} USD'\
                    .format(tx['type'], tx['usd'], tx['btc'], tx['fee'])
                self.tx_list.append(tx)
            if len(self.tx_list) == 0:
                self.error = 'no recent transactions found'
            return 1
        return 0

    def get_orders(self):
        params = {'user': self.user, 'password': self.password}
        response = self._send_request(self.open_orders_url, params)
        self.orders_list = []
        if len(response) == 0:
            self.error = 'no open orders listed'
            return 1
        elif response and 'error' not in response:
            for order in response:
                o = {}
                if order['type'] == 0:
                    o['type'] = 'buy'
                elif order['type'] == 1:
                    o['type'] = 'sell'
                o['timestamp'] = str(order['datetime'])
                o['price'] = '$' + str(order['price']) + ' USD/BTC'
                o['amount'] = str(round(float(order['amount']),1)) + ' BTC'
                o['id'] = str(order['id'])
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

        params = [('user', self.user),
                  ('password', self.password),
                  ('id', order_id),
                  ('type', order_type)]
        response = self._send_request(self.cancel_url, params)
        
        if response and 'error' not in response:
            self.cancelled_id = order_id
            self.cancelled_time = str(datetime.datetime.now()).split('.')[0]
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def withdraw(self, amount, address):
        params = {'user': self.user, 
                  'password': self.password, 
                  'amount': str(amount), 
                  'address': str(address)}
        response = self._send_request(self.withdraw_url, params)
        if response and 'error' not in response:
            self.timestamp = str(datetime.datetime.now())
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def deposit(self):
        params = {'user': self.user, 'password': self.password}
        response = self._send_request(self.deposit_url, params)
        if response and 'error' not in response:
            self.address = response
            return 1
        elif response and 'error' in response:
            self.error = str(response['error'])
            return 1
        return 0

    def get_lag(self):
        self.error = 'not available from this API'
        return 1

if __name__ == '__main__':
    bitstamp = PrivateBitstamp()
    bitstamp.get_info()
    # print bitstamp.usd_balance
    # print bitstamp.usd_balance
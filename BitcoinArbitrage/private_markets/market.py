import sys
sys.path.append('../')
sys.path.append('.')
from BitcoinArbitrage import config

class Market(object):
    config = config

    def __init__(self):
        self.name = self.__class__.__name__
        self.btc_balance = 0
        self.usd_balance = 0

    ## Abstract methods
    def buy(self, price, amount):
        pass

    def sell(self, price, amount):
        pass

    def get_info(self):
        pass

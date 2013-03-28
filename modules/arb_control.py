#!/usr/bin/env python
"""
btc-arbitrage module
Kyle Fitzsimmons 2013, http://kylefitz.com/
"""
import os
from BitcoinArbitrage import control

def arb_balance(phenny, input):
    if input == ".balance":
        phenny.say("Getting balances from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".balance" command from string

    for market in markets:
	    try:
		    balance_object = control.get_balance(market)
		    usd_float = round(balance_object.usd_balance, 4)
		    btc_float = round(balance_object.btc_balance, 4)
		    usd = " " * (8-len(str(usd_float))) + str(usd_float)
		    btc = " " * (7-len(str(btc_float))) + str(btc_float)
		    balance_output = market + " > USD: " + usd + " | BTC: " + btc
		    phenny.say(balance_output)
	    except:
		    phenny.say("Please check exchange initialism.")

arb_balance.commands = ['balance', 'bal']
arb_balance.name = 'arb_balance'


if __name__ == "__main__":
    print __doc__.strip()

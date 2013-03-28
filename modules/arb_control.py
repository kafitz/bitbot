#!/usr/bin/env python
"""
btc-arbitrage module
Kyle Fitzsimmons 2013, http://kylefitz.com/
"""
import os
from BitcoinArbitrage import irc_control

def arb_balance(bitbot, input):
    if input == ".balance":
        bitbot.say("Getting balances from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".balance" command from string

    for market in markets:
	    try:
		    balance_object = irc_control.get_balance(market)
		    usd_float = round(balance_object.usd_balance, 4)
		    btc_float = round(balance_object.btc_balance, 4)
		    usd = " " * (8-len(str(usd_float))) + str(usd_float)
		    btc = " " * (7-len(str(btc_float))) + str(btc_float)
		    balance_output = market + " > USD: " + usd + " | BTC: " + btc
		    bitbot.say(balance_output)
	    except:
		    bitbot.say("Please check exchange initialism.")

arb_balance.commands = ['balance', 'bal']
arb_balance.name = 'arb_balance'


if __name__ == "__main__":
    print __doc__.strip()

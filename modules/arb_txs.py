#!/usr/bin/env python
"""
btc-arbitrage module
Kyle Fitzsimmons 2013, http://kylefitz.com/
"""
import os
from BitcoinArbitrage.irc_scripts import txs

def arb_balance(phenny, input):
    if input == ".txs":
        phenny.say("Getting transactions from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".txs" command from string

    for market in markets:
	    try:
		    balance_object = balance.get_balance(market)
		    usd_float = round(balance_object.usd_balance,4)
		    btc_float = round(balance_object.btc_balance,4)
		    usd = " " * (8-len(str(usd_float))) + str(usd_float)
		    btc = " " * (7-len(str(btc_float))) + str(btc_float)
		    balance_output = market + " > USD: " + usd + " | BTC: " + btc
		    phenny.say(balance_output)
	    except:
		    phenny.say("Please check exchange initialism.")

arb_txs.commands = ['txs']
arb_txs.name = 'arb_txs'


if __name__ == "__main__":
    print __doc__.strip()

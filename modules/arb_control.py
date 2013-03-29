#!/usr/bin/env python
"""
btc-arbitrage module
Kyle Fitzsimmons 2013, http://kylefitz.com/
"""
import os
from BitcoinArbitrage import irc_control

def arb_balance(bitbot, input):
    if input[1:] in arb_balance.commands:
        bitbot.say("Getting balances from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".balance" command from string
    
    for market in markets:
	    balance_object = irc_control.get_balance(market)
	    usd_float = round(balance_object.usd_balance, 4)
	    btc_float = round(balance_object.btc_balance, 4) 
	    usd = " " * (8-len(str(usd_float))) + str(usd_float)
	    btc = " " * (7-len(str(btc_float))) + str(btc_float)
	    balance_output = market + " > USD: " + usd + " | BTC: " + btc
	    bitbot.say(balance_output)

arb_balance.commands = ['balance', 'bal']
arb_balance.name = 'arb_balance'

def open_orders(bitbot, input):
    if input[1:] in open_orders.commands:
        bitbot.say("Getting open orders from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ]

    for market in markets:
	    order_object = irc_control.open_orders(market)
	    order_output = market + " > " + str(order_object)
	    bitbot.say(order_output)


open_orders.commands = ['openorders']
open_orders.name = 'open_orders'

def transactions(bitbot, input):
    if input[1:] in transactions.commands:
        bitbot.say("Getting transactions from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ]

    for market in markets:
	    transactions_object = irc_control.transactions(market)
	    for transaction in transactions_object:
	        bitbot.say(str(transaction))
	    transactions_output = market + " > " + str(transactions_object)
	    bitbot.say(transactions_output)


transactions.commands = ['transactions','txs']
transactions.name = 'transactions'


if __name__ == "__main__":
    print __doc__.strip()

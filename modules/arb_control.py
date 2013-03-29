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

def transactions(bitbot, input):
    if input[1:] in transactions.commands:
        bitbot.say("Getting transactions from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ]

    for market in markets:
        transactions_object = irc_control.transactions(market)
        # for transaction in transactions_object:
        bitbot.say(transactions_object.name + " transactions:")
        for transaction_dict in transactions_object.tx_list:
            if transaction_dict['type'] == 0:
                tx_type = 'deposit'
            elif transaction_dict['type'] == 1:
                tx_type = 'withdrawal'
            elif transaction_dict['type'] == 2:
                if transaction_dict['usd'] < 0:
                    tx_type = 'buy'
                elif transaction_dict['usd'] > 0:
                    tx_type = 'sell'
            if tx_type in ['buy', 'sell']:
                transactions_output = market + " > " + str(transaction_dict['datetime']) + ": " +\
                    tx_type + " $" + str(abs(transaction_dict['usd'])) + " for " + str(transaction_dict['btc']) +\
                    ". Fee of: " + str(transaction_dict['fee'])
            elif tx_type in ['deposit', 'withdrawal']:
                if int(transaction_dict['usd']) != 0:
                    tx_amount = transaction_dict['usd']
                    tx_currency = "USD"
                elif int(transaction_dict['btc']) != 0:
                    tx_amount = transaction_dict['btc']
                    tx_currency = "BTC"
                transactions_output = market + " > " + str(transaction_dict['datetime']) + ": " +\
                    str(tx_type) + " of " + str(tx_amount) + " " + str(tx_currency) + ". "
            bitbot.say(transactions_output)

def open_orders(bitbot, input):
    if input[1:] in open_orders.commands:
        bitbot.say("Getting open orders from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ]

    # for market in markets:
    #     order_object = irc_control.open_orders(market)
    #     for order in order_object.orders_list:
    #         # order_output = market + " > " + order['datetime'] + ": " + order_object[] + " " + order_object.type
    #         bitbot.say(str(order))


open_orders.commands = ['open', 'openorders']
open_orders.name = 'open_orders'


transactions.commands = ['transactions','txs']
transactions.name = 'transactions'


if __name__ == "__main__":
    print __doc__.strip()

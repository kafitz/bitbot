#!/usr/bin/env python
"""
module to control the BitcoinArbitrage project from IRC

Kyle Fitzsimmons 2013, http://kylefitz.com/
Bas Pennewaert 2013, bas@pennewaert.com

start_arbitrage ->  start the arbitrage script, looking for opportunities on all public_markets
balance         ->  balances from private_markets: usd_balance, btc_balance
transactions    ->  transactions from private_markets: 
open_orders     ->  currently open orders from private_markets:

"""
from BitcoinArbitrage import arbitrage
from BitcoinArbitrage import irc_control

def start_arbitrage(bitbot, input):
    bitbot.say("Starting up btc-arbitrage...")
    arbitrer = arbitrage.Arbitrer()
    while True:
        arbitrer.loop(bitbot)
        
start_arbitrage.commands = ['arb','arbitrage']
start_arbitrage.name = 'start_arbitrage'


def balance(bitbot, input):
    if input[1:] in balance.commands:
        bitbot.say("Getting balances from all exchanges")
        markets = ['mtgx','bflr','bstp','bctl']
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".balance" command from string
    
    for market in markets:
        try:
            balance_object = irc_control.get_balance(market)
            usd_str = str(round(balance_object.usd_balance, 4))
            btc_str = str(round(balance_object.btc_balance, 4))
            bitbot.say(market + " > USD: {0:7} | BTC: {1:7}".format(usd_str,btc_str))
        except:
            bitbot.say(market + " > Something went wrong here.")
            
balance.commands = ['balance', 'bal']
balance.name = 'balance'

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
        for transaction in transactions_object.tx_list:
            print transaction['type']
            if transaction['type'] in ['buy', 'sell']:
                transactions_output = market + " > " + str(transaction['datetime']) + ": " +\
                    transaction['type'] + " $" + str(abs(transaction['usd'])) + " for " + str(transaction['btc']) +\
                    ". Fee of: " + str(transaction['fee'])
            elif transaction['type'] in ['deposit', 'withdrawal']:
                if int(transaction['usd']) != 0:
                    tx_amount = transaction['usd']
                    tx_currency = "USD"
                elif int(transaction['btc']) != 0:
                    tx_amount = transaction['btc']
                    tx_currency = "BTC"
                transactions_output = market + " > " + str(transaction['datetime']) + ": " +\
                    str(transaction['type']) + " of " + str(tx_amount) + " " + str(tx_currency) + ". "
            bitbot.say(transactions_output)

transactions.commands = ['transactions','txs']
transactions.name = 'transactions'            


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


if __name__ == "__main__":
    print __doc__.strip()

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
from BitcoinArbitrage import arbitrage # arbitrage script
from BitcoinArbitrage import config # read the config file
from BitcoinArbitrage import private_markets # load private APIs

def start_arbitrage(bitbot, input):
    bitbot.say("Starting up btc-arbitrage...")
    arbitrer = arbitrage.Arbitrer()
    while True:
        arbitrer.loop(bitbot)
        
start_arbitrage.commands = ['arb','arbitrage']
start_arbitrage.name = 'start_arbitrage'

def load(input):
    market_name = config.private_markets[input]
    exec('import BitcoinArbitrage.private_markets.' + market_name.lower())
    market = eval('private_markets.' + market_name.lower() + '.Private' + market_name + '()')
    return market

def balance(bitbot, input):
    if input[1:] in balance.commands:
        bitbot.say("Getting balances from all exchanges")
        markets = sorted(config.private_markets.keys())
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".balance" command from string
    
    for market in markets:
#        try:
        market_obj = load(market) # load the correct market object (mo)
        market_obj.get_info()            # execute the relevant function
        if market_obj.error:
            bitbot.say(market + " > " + market_obj.errormsg)
            return
            
        usd_str = str(round(market_obj.usd_balance, 4))
        btc_str = str(round(market_obj.btc_balance, 4))
        bitbot.say(market + " > USD: {0:7} | BTC: {1:7}".format(usd_str, btc_str))
#        except:
#           bitbot.say(market + " > Something went wrong here.")
            
balance.commands = ['balance', 'bal']
balance.name = 'balance'

def transactions(bitbot, input):
    if input[1:] in transactions.commands:
        bitbot.say("Getting transactions from all exchanges")
        markets = sorted(config.private_markets.keys())
    else:
        markets = [ input.split(" ", 1)[1] ]

    for market in markets:
        market_obj = load(market)
        market_obj.get_txs()
        bitbot.say(market_obj.name + " transactions:")
        for transaction in market_obj.tx_list:
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
        markets = sorted(config.private_markets.keys())
    else:
        markets = [ input.split(" ", 1)[1] ]

    for market in markets:
        market_obj = load(market)
        market_obj.get_orders()
        for order in market_obj.orders_list:
            # Attempt to deal with unicode issues from difference encodings at different exchanges
            order_output = market + u" > " + order["datetime"] + u": " + order["type"] + u" " +\
                order["amount"] + u" for " + order["price"] + u". "
            bitbot.say(order_output)

open_orders.commands = ['open', 'openorders']
open_orders.name = 'open_orders'


if __name__ == "__main__":
    print __doc__.strip()

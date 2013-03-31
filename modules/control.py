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

def load(initials):
    market_name = config.private_markets[initials]
    exec('import BitcoinArbitrage.private_markets.' + market_name.lower())
    market = eval('private_markets.' + market_name.lower() + '.Private' + market_name + '()')
    
    return market

def balance(bitbot, input):
    if input[1:] in balance.commands:
        bitbot.say("Getting balances from all exchanges:")
        markets = sorted(config.private_markets.keys())
    else:
        markets = [ input.split(" ", 1)[1] ] # remove ".balance" command from string
    
    for market in markets:
        market_obj = load(market) # load the correct market object (mo)
        market_obj.get_info()            # execute the relevant function
        if market_obj.error:
            bitbot.say(market + " > " + market_obj.errormsg)
            return
            
        usd_str = str(round(market_obj.usd_balance, 4))
        btc_str = str(round(market_obj.btc_balance, 4))
        bitbot.say(market + " > USD: {0:7} | BTC: {1:7}".format(usd_str, btc_str))
            
balance.commands = ['balance', 'bal']
balance.name = 'balance'

def transactions(bitbot, input):
    order_id = None
    if input[1:] in transactions.commands:
        bitbot.say("Getting transactions from all exchanges")
        markets = sorted(config.private_markets.keys())
    else:
        parameters = input.split(" ")[1:]
        markets = [ parameters[0] ]
        try:
            order_id = parameters[1]
        except: pass

    for market in markets:
        market_obj = load(market)
        response = market_obj.get_txs(order_id)
        # Out of place error handling, find better solution
        if len(market_obj.tx_list) == 0:
            try:
                bitbot.say(response)
            except:
                bitbot.say("No recent Bitstamp transactions found.")
            return
        bitbot.say(market_obj.name + " transactions:")
        for transaction in market_obj.tx_list:
            if transaction['type'] in ['buy', 'sell']:
                transactions_output = market + " > " + str(transaction['timestamp']) + ": " +\
                    transaction['type'] + " $" + str(abs(transaction['usd'])) + " for " + str(transaction['btc']) +\
                    ". Fee of: " + str(transaction['fee'])
            elif transaction['type'] in ['deposit', 'withdrawal']:
                if int(transaction['usd']) != 0:
                    tx_amount = transaction['usd']
                    tx_currency = "USD"
                elif int(transaction['btc']) != 0:
                    tx_amount = transaction['btc']
                    tx_currency = "BTC"
                transactions_output = market + " > " + str(transaction['timestamp']) + ": " +\
                    str(transaction['type']) + " of " + str(tx_amount) + " " + str(tx_currency) + ". "
            bitbot.say(transactions_output)

transactions.commands = ['transactions','txs']
transactions.name = 'transactions'            


def open_orders(bitbot, input):
    if input[1:] in open_orders.commands:
        bitbot.say("Getting open orders from all exchanges:")
        markets = sorted(config.private_markets.keys())
    else:
        markets = input.split(" ")[1:] # Create a list of specified exchanges

    for market in markets:
        try:
            market_obj = load(market)
        except:
            bitbot.say('Error - open_orders: invalid exchange specified - "' + str(market) + '".')
            return
        market_obj.get_orders()
        
        if market_obj.error:
            bitbot.say(market + " > " + market_obj.errormsg)
        else:
            for order in market_obj.orders_list:
                # Attempt to deal with unicode issues from difference encodings at different exchanges
                order_output = market + u" > " + order["timestamp"] + u": " + order["type"] + u" " +\
                    order["amount"] + u" for " + order["price"] + u". id: " + order["id"]

                bitbot.say(order_output)

open_orders.commands = ['open', 'openorders']
open_orders.name = 'open_orders'

def cancel_order(bitbot, input):
    if input[1:] in cancel_order.commands:
        bitbot.say("Error: must provide exchange and order ID with cancel function. (.cancel exchange #order_id)")
        return
    input_list = input.split(" ")
    market = input_list[1]
    try:
        order_id = input_list[2]
    except:
        bitbot.say("Error - cancel_order: invalid # of arguments specified. (.cancel exchange #order_id)")
        return
    try:
        market_obj = load(market)
    except:
        bitbot.say('Error - cancel_order: invalid exchange specified - "' + str(market) + '".')
        return
        
    return_output = market_obj.cancel(order_id)
    if return_output == 1:
        bitbot.say(market + " > cancel > order " + market_obj.cancelled_id + " successfully cancelled at " + market_obj.cancelled_time)
    else:
        bitbot.say(market + " > cancel > error: " + str(return_output))

cancel_order.commands = ['cancel']
cancel_order.name = 'cancel_order'

def buy(bitbot, input):
    pass


if __name__ == "__main__":
    print __doc__.strip()

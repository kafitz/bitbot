#!/usr/bin/env python
'''
module to control the BitcoinArbitrage project from IRC

Kyle Fitzsimmons 2013, http://kylefitz.com/
Bas Pennewaert 2013, bas@pennewaert.com

start_arbitrage ->  start the arbitrage script, looking for opportunities on all public_markets
balance         ->  balances from private_markets: usd_balance, btc_balance
transactions    ->  transactions from private_markets: 
open_orders     ->  currently open orders from private_markets:
cancel_order    ->  cancel an open order
buy             ->  place a buy order
sell            ->  place a sell order
deposit         ->  get the bitcoin deposit address
withdraw        ->  withdraw bitcoin from exchange
'''

from BitcoinArbitrage import arbitrage          # arbitrage script
from BitcoinArbitrage import config             # read the config file
from BitcoinArbitrage import private_markets    # load private APIs
from decimal import Decimal

def start_arbitrage(bitbot, input):
    bitbot.say('arb > starting up...')
    arbitrer = arbitrage.Arbitrer()
    while True:
        arbitrer.loop(bitbot)
        
start_arbitrage.commands = ['arb','arbitrage']
start_arbitrage.name = 'start_arbitrage'

# load the correct market, given its initials
def load(initials):
    try: 
        market_name = config.private_markets[initials]
    except KeyError:
        return 1, 'exchange initials not found in config'     
    exec('import BitcoinArbitrage.private_markets.' + market_name.lower())
    market = eval('private_markets.' + market_name.lower() + '.Private' + market_name + '()')   
    return 0, market

# determine which markets to query  
def which(input,commands):
    if input[1:] in commands:
        markets = sorted(config.private_markets.keys())
    else:
        markets = [ input.split(' ', 1)[1] ]
    return markets

def balance(bitbot, input):
    markets = which(input,balance.commands) 
    bitbot.say('bal > Getting balance from ' + ', '.join(markets) + ':')  
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.get_info()               # execute the relevant function
        elif error == 1:                        # an error occured
            bitbot.say('bal > ' + market + ' > ' + market_obj)
            return 0

        if market_obj.error == '':
            usd_str = str(round(market_obj.usd_balance, 3))
            btc_str = str(round(market_obj.btc_balance, 3))
            bitbot.say('bal > ' + market + ' > USD: {0:7} | BTC: {1:7}'.format(usd_str, btc_str))
        else:
            bitbot.say('bal > ' + market + ' > ' + market_obj.error)
            
balance.commands = ['balance', 'bal']
balance.name = 'balance'

def transactions(bitbot, input):
    order_id = None
    if input[1:] in transactions.commands:
        bitbot.say('txs > Getting transactions from all exchanges')
        markets = sorted(config.private_markets.keys())
    else:
        parameters = input.split(' ')[1:]
        markets = [ parameters[0] ]
        try:
            order_id = parameters[1]
        except: pass

    for market in markets:
        error, market_obj = load(market)                # load the correct market object
        if error == 0:                                  # market was loaded without errors
            response = market_obj.get_txs(order_id)     # execute the relevant function
        elif error == 1:                                # an error occured
            bitbot.say('txs > ' + market + ' > ' + market_obj)
            return 0
        
        # Out of place error handling, find better solution
        if len(market_obj.tx_list) == 0:
            try:
                bitbot.say(response)
            except:
                bitbot.say('txs > ' + market + 'no recent transactions found')
            return
        bitbot.say(market + ' transactions:')
        for transaction in market_obj.tx_list:
            if transaction['type'] in ['buy', 'sell']:
                transactions_output = 'txs > ' + market + ' > ' + str(transaction['timestamp']) + ': ' +\
                    transaction['type'] + ' $' + str(abs(float(transaction['usd']))) + ' for ' + str(transaction['btc']) +\
                    '. Fee of: $' + str(transaction['fee'])
            elif transaction['type'] in ['deposit', 'withdrawal']:
                if float(transaction['usd']) != 0.0:
                    tx_amount = float(transaction['usd'])
                    tx_currency = 'USD'
                elif float(transaction['btc']) != 0.0:
                    tx_amount = float(transaction['btc'])
                    tx_currency = 'BTC'
                transactions_output = 'txs > ' + market + ' > ' + str(transaction['timestamp']) + ': ' +\
                    str(transaction['type']) + ' of ' + str(tx_amount) + ' ' + str(tx_currency) + '. '
            bitbot.say(transactions_output)

transactions.commands = ['transactions','txs']
transactions.name = 'transactions'            


def open_orders(bitbot, input):
    markets = which(input,open_orders.commands)
    bitbot.say('open > Getting open orders from ' + ', '.join(markets) + ':')  
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.get_orders()             # execute the relevant function
        elif error == 1:                        # an error occured
            bitbot.say('open > ' + market + ' > ' + market_obj)
            return 0
      
        if market_obj.error == '':
            for order in market_obj.orders_list:
                # Attempt to deal with unicode issues from difference encodings at different exchanges
                order_output = 'open > ' + market + u' > ' + order['timestamp'] + u': ' + order['type'] + u' ' +\
                    order['amount'] + u' for ' + order['price'] + u'. id: ' + order['id']
                bitbot.say(order_output)
        else:
            bitbot.say('open > ' + market + ' > ' + market_obj.error)
          

open_orders.commands = ['open', 'openorders']
open_orders.name = 'open_orders'

def cancel_order(bitbot, input):
    # Test input formatting
    if input[1:] in cancel_order.commands:
        bitbot.say('cancel > ' + 'must provide exchange and order ID with cancel function: .cancel exchange #order_id')
        return
    input_list = input.split(' ')
    market = input_list[1]
    try:
        order_id = input_list[2]
    except:
        bitbot.say('Error - cancel_order: invalid # of arguments specified. (.cancel exchange #order_id)')
        return
        
    error, market_obj = load(market)                    # load the correct market object
    if error == 0:                                      # market was loaded without errors
        return_output = market_obj.cancel(order_id)     # execute the relevant function
    elif error == 1:                                    # an error occured
        bitbot.say('cancel > ' + market + ' > ' + market_obj)
        return 0
    
    if market_obj.error == '':
        bitbot.say('cancel > ' + market + ' > order ' + market_obj.cancelled_id + ' [' + market_obj.cancelled_amount + '] cancelled at ' + market_obj.cancelled_time)
    else:
        bitbot.say('cancel > ' + market + ' > error: ' + str(market_obj.error))

cancel_order.commands = ['cancel']
cancel_order.name = 'cancel_order'

def buy(bitbot, input):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        bitbot.say('buy > insufficient parameters: .buy exchange BTC_total $price_limit_per_btc')
        return
    market = parameters[0]
    total_usd = Decimal(parameters[1])
    price_limit = Decimal(parameters[2])
    
    error, market_obj = load(market)                                # load the correct market object
    if error == 0:                                                  # market was loaded without errors
        return_output = str(market_obj.buy(total_usd, price_limit))  # execute the relevant function
        bitbot.say('buy > ' + market + ' > ' + return_output)            
        return 1
    elif error == 1:                                            # an error occured
        bitbot.say('buy > ' + market + ' > ' + market_obj)
        return 0

buy.commands = ['buy']
buy.name = 'buy'


def sell(bitbot, input):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        bitbot.say('sell > insufficient parameters: .sell exchange $USD_total $price_limit_per_btc')
        return
    market = parameters[0]
    total_usd = str(parameters[1])
    price_limit = str(parameters[2])
    
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        return_output = market_obj.sell(total_usd, price_limit) # execute the relevant function
        bitbot.say('sell > ' + market + ' > ' + return_output)            
        return 1
    elif error == 1:                                            # an error occured
        bitbot.say('sell > ' + market + ' > ' + market_obj)
        return 0

sell.commands = ['sell']
sell.name = 'sell'

def deposit(bitbot, input):
    markets = which(input, deposit.commands) 
    bitbot.say('dep > Getting deposit address from ' + ', '.join(markets) + ':')  
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.deposit()                # execute the relevant function
        elif error == 1:                        # an error occured
            bitbot.say('dep > ' + market + ' > ' + market_obj)
            return 0

        
        if market_obj.error == '':
            bitbot.say('dep > ' + market + ' > address: ' + market_obj.address)
        else:
            bitbot.say('dep > ' + market + ' > ' + market_obj.error) 
            
deposit.commands = ['deposit','dep']
deposit.name = 'deposit'     
       
            
def withdraw(bitbot, input):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        bitbot.say('wdw > insufficient parameters: .wdw exchange amount address')
        return
    market = parameters[0]
    amount = parameters[1]
    address = parameters[2]
    
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        market_obj.withdraw(amount, address)    # execute the relevant function          
    elif error == 1:                                            # an error occured
        bitbot.say('wdw > ' + market + ' > ' + market_obj)
        return 0
    if market_obj.error == '':
        bitbot.say('wdw > ' + market + ' > ' + market_obj.status)
    else:
        bitbot.say('wdw > ' + market + ' > ' + market_obj.error)
            
withdraw.commands = ['withdraw','wdw']
withdraw.name = 'withdraw'

if __name__ == '__main__':
    print __doc__.strip()

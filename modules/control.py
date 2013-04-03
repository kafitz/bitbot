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
    markets = which(input,transactions.commands) 
    bitbot.say('bal > Getting transactions from ' + ', '.join(markets) + ':')  
    for market in markets:
        error, market_obj = load(market)                # load the correct market object
        if error == 0:                                  # market was loaded without errors
            market_obj.get_txs()     # execute the relevant function
        elif error == 1:                                # an error occured
            bitbot.say('txs > ' + market + ' > ' + market_obj)
            return 0        
        if market_obj.error == '':
            for transaction in market_obj.tx_list:
                output = 'txs > {0} > {1}: {2} '.format(market, transaction['timestamp'], transaction['desc'])
                bitbot.say(output)
        else:
            bitbot.say('txs > ' + market + ' > ' + market_obj.error)

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
                    order['amount'] + u' for ' + order['price'] + u' [' + order['id'] + ']'
                bitbot.say(order_output)
        else:
            bitbot.say('open > ' + market + ' > ' + market_obj.error)
          

open_orders.commands = ['open', 'openorders']
open_orders.name = 'open_orders'

def cancel_order(bitbot, input):
    # Test input formatting
    if input[1:] in cancel_order.commands:
        bitbot.say('cancel > invalid # of arguments specified: .cancel exchange #order_id')
        return
    input_list = input.split(' ')
    market = input_list[1]
    try:
        order_id = input_list[2]
    except:
        bitbot.say('cancel > ' + market + ' > invalid # of arguments specified: .cancel exchange #order_id')
        return
        
    error, market_obj = load(market)                    # load the correct market object
    if error == 0:                                      # market was loaded without errors
        market_obj.cancel(order_id)     # execute the relevant function
    elif error == 1:                                    # an error occured
        bitbot.say('cancel > ' + market + ' > ' + market_obj)
        return 0
    
    if market_obj.error == '':
        bitbot.say('cancel > ' + market + ' > ' + market_obj.cancelled_time + ': cancelled ' + market_obj.cancelled_amount + ' [' + market_obj.cancelled_id + '] ')
    else:
        bitbot.say('cancel > ' + market + ' > error: ' + str(market_obj.error))

cancel_order.commands = ['cancel']
cancel_order.name = 'cancel_order'

def buy(bitbot, input):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        bitbot.say('buy > invalid # of arguments specified: .buy exchange BTC_total $price_limit_per_btc')
        return
    market = parameters[0]
    total_btc = Decimal(parameters[1])
    price_limit = Decimal(parameters[2])
    
    error, market_obj = load(market)                                # load the correct market object
    if error == 0:                                                  # market was loaded without errors
        market_obj.buy(total_btc, price_limit)                      # execute the relevant function
    elif error == 1:                                                # an error occured
        bitbot.say('buy > ' + market + ' > ' + market_obj)
        return 0
        
    if market_obj.error == '':
        bitbot.say('buy > ' + market + ' > ' + market_obj.timestamp + ': bid ' + market_obj.amount + ' BTC for ' +\
            market_obj.price + ' USD/BTC placed [' + market_obj.id + ']')  
    else: 
        bitbot.say('buy > ' + market + ' > error: ' + market_obj.error) 
        return 1

buy.commands = ['buy']
buy.name = 'buy'


def sell(bitbot, input):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        bitbot.say('sell > invalid # of arguments specified: .sell exchange $USD_total $price_limit_per_btc')
        return
    market = parameters[0]
    total_usd = str(parameters[1])
    price_limit = str(parameters[2])
    
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        market_obj.sell(total_usd, price_limit)                 # execute the relevant function
    elif error == 1:                                            # an error occured
        bitbot.say('sell > ' + market + ' > ' + market_obj)
        return 0
        
    if market_obj.error == '':
        bitbot.say('sell > ' + market + ' > ' + market_obj.timestamp + ': ask ' + market_obj.amount + ' BTC for ' +\
            market_obj.price + ' USD/BTC placed [' + market_obj.id + ']')  
    else: 
        bitbot.say('sell > ' + market + ' > error: ' + market_obj.error) 
        return 1
        
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
            bitbot.say('dep > ' + market + ' > error: ' + market_obj.error) 
            
deposit.commands = ['deposit','dep']
deposit.name = 'deposit'     
       
            
def withdraw(bitbot, input):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        bitbot.say('wdw > invalid # of arguments specified: .wdw exchange amount address')
        return
    market = parameters[0]
    amount = parameters[1]
    address = parameters[2]
    
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        market_obj.withdraw(amount, address)                    # execute the relevant function          
    elif error == 1:                                            # an error occured
        bitbot.say('wdw > ' + market + ' > ' + market_obj)
        return 0
        
    if market_obj.error == '':
        bitbot.say('wdw > ' + market + ' > ' + market_obj.timestamp + ': withdrawal processed')
    else:
        bitbot.say('wdw > ' + market + ' > ' + market_obj.error)
            
withdraw.commands = ['withdraw','wdw']
withdraw.name = 'withdraw'

if __name__ == '__main__':
    print __doc__.strip()

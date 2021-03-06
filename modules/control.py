#!/usr/bin/env python
# coding=utf-8
'''
module to control the BitcoinArbitrage project from IRC

Kyle Fitzsimmons 2013, http://kylefitz.com/
Bas Pennewaert 2013, bas@pennewaert.com

start_arbitrage ->  start the arbitrage script, looking for opportunities on all public_markets
balance         ->  balances from private_markets: usd_balance, btc_balance
transactions    ->  get previous transactions from private_markets
open_orders     ->  currently open orders from private_markets
cancel_order    ->  cancel an open order
buy             ->  place a buy order
sell            ->  place a sell order
deposit         ->  get the bitcoin deposit address
withdraw        ->  withdraw bitcoin from exchange
deal            ->  execute an arbitrage deal
lag             ->  get lag from trade engine
'''

import threading
from decimal import Decimal
from collections import OrderedDict
import arbitrage          # arbitrage script
import config             # read the config file
import private_markets    # load private APIs

# output to IRC(True) or Terminal(False)
def irc(bitbot, msg, output=True):
    if output:
        bitbot.say(msg)
    else:
        print msg

# load the correct market, given its initials
def load(initials):
    try: 
        market_name = config.private_markets[initials]
    except KeyError:
        return 1, 'exchange initials not found in config'     
    exec('import private_markets.' + market_name.lower())
    market = eval('private_markets.' + market_name.lower() + '.Private' + market_name + '()')   
    return 0, market

# determine which markets to query  
def which(input,commands):
    if input[1:] in commands:
        markets = sorted(config.private_markets.keys())
    else:
        markets = [ input.split(' ', 1)[1] ]
    return markets
    
def start_arbitrage(bitbot, input):
    if bitbot.variables.get('arb') is True:
        bitbot.say('arb > already running')
    else:
        bitbot.variables['arb'] = True
        irc(bitbot,'arb > starting up...')
        bitbot.variables['arbitrer'] = arbitrage.Arbitrer()
        arbitrer = bitbot.variables['arbitrer']
        arbitrer.loop(bitbot)
        
start_arbitrage.commands = ['arb','arbitrage']
start_arbitrage.name = 'start_arbitrage'

def balance(bitbot, input, output=True):
    markets = which(input, balance.commands)
    irc(bitbot, 'bal > Getting balance from ' + ', '.join(markets) + ':', output)  
    def update_info(market_obj):
        market_obj.get_info()

    threads = []
    market_instances = OrderedDict()
    for market in markets:
        error, market_obj = load(market)                                # load the correct market object        
        if error == 0:                                                  # market was loaded without errors
            market_instances[market] = market_obj
            thread = threading.Thread(target=update_info, args=(market_obj,))
            thread.start()
            threads.append(thread)
        elif error == 1:                                                # an error occured
            irc(bitbot,'bal > ' + market + ' > ' + market_obj)
            return 0
    for thread in threads:
        thread.join()
    for market, market_obj in market_instances.items():
        if market_obj.error != '':
            irc(bitbot,'bal > ' + market + ' > error: ' + market_obj.error)
        else:
            if market_obj.usd_balance != None:
                try:
                    usd = str(round(market_obj.usd_balance,3))
                    usd_hold = str(round(market_obj.usd_hold,3))
                    btc = str(round(market_obj.btc_balance,4))
                    btc_hold = str(round(market_obj.btc_hold,4))      
                except AttributeError, e:
                    market_obj.error = str(e) # space for no output and avoiding next test

                if market_obj.error == '':
                    irc(bitbot,'bal > ' + market + ' > ${0:7} + {1:6} | B {2:6} + {3:5} | Fee: {4}' \
                        .format(usd, usd_hold, btc, btc_hold, round(float(market_obj.fee),2)))
                    if not output:
                        return usd, btc
    return
                
balance.commands = ['balance', 'bal']
balance.name = 'balance'

def transactions(bitbot, input, output=True):
    markets = which(input,transactions.commands) 
    irc(bitbot,'bal > Getting transactions from ' + ', '.join(markets) + ':')  
    for market in markets:
        error, market_obj = load(market)                # load the correct market object
        if error == 0:                                  # market was loaded without errors
            market_obj.get_txs()                        # execute the relevant function
        elif error == 1:                                # an error occured
            irc(bitbot,'txs > ' + market + ' > ' + market_obj)
            return 0        
        if market_obj.error == '':
            for transaction in market_obj.tx_list:
                output = 'txs > {0} > {1}: {2} '.format(market, transaction['timestamp'], transaction['desc'])
                irc(bitbot,output)
        else:
            irc(bitbot,'txs > ' + market + ' > ' + market_obj.error)

transactions.commands = ['transactions','txs']
transactions.name = 'transactions'            

def order_details(bitbot, input, output=True):
    if input[1:] in order_details.commands:
        irc(bitbot,'order > usage: .order #order_id')
        return
    parameters = input.split(' ')[1:]
    market = parameters[0]
    order_id = parameters[1]
    
    error, market_obj = load(market)        # load the correct market object
    if error == 0:                          # market was loaded without errors
        market_obj.order_details(order_id)             # execute the relevant function
    elif error == 1:                        # an error occured
        irc(bitbot,'order > ' + market + ' > error: ' + market_obj)
        return 0

    if market_obj.error == '': 
        irc(bitbot,'order > ' + market + ' > ' + market_obj.status + ': ' + market_obj.type + u' ' +\
            market_obj.amount + ' for ' + market_obj.price,output)
    else:
        irc(bitbot,'order > ' + market + ' > error: ' + market_obj.error,output)
    return       

order_details.commands = ['order', 'order_details', 'o']
order_details.name = 'order_details'

def open_orders(bitbot, input, output=True):
    markets = which(input,open_orders.commands)
    irc(bitbot,'open > Getting open orders from ' + ', '.join(markets) + ':',output)
    orders = {}
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.get_orders()             # execute the relevant function
        elif error == 1:                        # an error occured
            irc(bitbot,'open > ' + market + ' > error: ' + market_obj)
            return 0

        if market_obj.error == '':
            for order in market_obj.orders_list:
                # Attempt to deal with unicode issues from difference encodings at different exchanges
                order_string = 'open > ' + market + u' > ' + order['type'] + u' ' +\
                    order['amount'] + u' for ' + order['price'] + u': ' + order['id']
                irc(bitbot,order_string,output)
                orders[order['id']] = market
        else:
            irc(bitbot,'open > ' + market + ' > ' + market_obj.error,output)
    return orders          

open_orders.commands = ['open', 'openorders']
open_orders.name = 'open_orders'

def cancel_order(bitbot, input, output=True):
    # Test input formatting
    if input[1:] in cancel_order.commands:
        irc(bitbot,'cancel > usage: .cancel #order_id')
        return
        
    input_list = input.split(' ')
    order_id = input_list[1] 
    
    orders = open_orders(bitbot,'.open',False) 
    if order_id in orders.keys():
        market = orders[order_id]
    else:
        irc(bitbot,'cancel > error: order id not found')
        return
        
    error, market_obj = load(market)                    # load the correct market object
    if error == 0:                                      # market was loaded without errors
        market_obj.cancel(order_id)                     # execute the relevant function
    elif error == 1:                                    # an error occured
        irc(bitbot,'cancel > ' + market + ' > ' + market_obj)
        return 0
        
    if market_obj.error == '':
        irc(bitbot,'cancel > ' + market + ' > cancelled ' + market_obj.cancelled_amount + ': ' + market_obj.cancelled_id)
    else:
        irc(bitbot,'cancel > ' + market + ' > error: ' + str(market_obj.error))

cancel_order.commands = ['cancel']
cancel_order.name = 'cancel_order'

def buy(bitbot, input, output=True):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        irc(bitbot,'buy > invalid # of arguments specified: .buy exchange BTC_total $price_limit_per_btc')
        return
    market = parameters[0]
    total_btc = Decimal(parameters[1])
    price_limit = Decimal(parameters[2])
    
    error, market_obj = load(market)                                # load the correct market object
    if error == 0:                                                  # market was loaded without errors
        market_obj.buy(total_btc, price_limit)                      # execute the relevant function
    elif error == 1:                                                # an error occured
        irc(bitbot,'buy > ' + market + ' > ' + market_obj)
        return 0
        
    if market_obj.error == '':
        irc(bitbot,'buy > ' + market + ' > bid ' + str(market_obj.amount) + ' BTC for ' +\
            str(market_obj.price) + ' USD/BTC placed: ' + market_obj.id)  
    else: 
        irc(bitbot,'buy > ' + market + ' > error: ' + market_obj.error) 
        return 1

buy.commands = ['buy']
buy.name = 'buy'


def sell(bitbot, input, output=True):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        irc(bitbot,'sell > invalid # of arguments specified: .sell exchange BTC_total $price_limit_per_btc')
        return
    market = parameters[0]
    total_usd = str(parameters[1])
    price_limit = str(parameters[2])
    
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        market_obj.sell(total_usd, price_limit)                 # execute the relevant function
    elif error == 1:                                            # an error occured
        irc(bitbot,'sell > ' + market + ' > ' + market_obj)
        return 0
        
    if market_obj.error == '':
        irc(bitbot,'sell > ' + market + ' > ' + market_obj.timestamp + ': ask ' + market_obj.amount + ' BTC for ' +\
            market_obj.price + ' USD/BTC placed [' + market_obj.id + ']')  
    else: 
        irc(bitbot,'sell > ' + market + ' > error: ' + market_obj.error) 
        return 1
        
sell.commands = ['sell']
sell.name = 'sell'

def deposit(bitbot, input, output=True):
    markets = which(input, deposit.commands) 
    irc(bitbot,'dep > Getting deposit address from ' + ', '.join(markets) + ':',output)  
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.deposit()                # execute the relevant function
        elif error == 1:                        # an error occured
            irc(bitbot,'dep > ' + market + ' > ' + market_obj)
            return 1
        if market_obj.error == '':
            irc(bitbot,'dep > ' + market + ' > address: ' + 'https://blockchain.info/address/' + market_obj.address + ' ' + market_obj.address, output)
            return market_obj.address
        else:
            irc(bitbot,'dep > ' + market + ' > error: ' + market_obj.error) 

            
deposit.commands = ['deposit','dep']
deposit.name = 'deposit'     

            
def withdraw(bitbot, input, output=True):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        irc(bitbot,'wdw > usage: .wdw market amount address | .wdw market amount market',output)
        return
    market = parameters[0]
    amount = parameters[1]
    if len(parameters[2]) == 34:
        address = parameters[2]
    else:
        address = deposit(bitbot,'.dep {}'.format(parameters[2]),False)
 
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        market_obj.withdraw(amount, address)                    # execute the relevant function          
    elif error == 1:                                            # an error occured
        irc(bitbot,'wdw > ' + market + ' > ' + market_obj)
        return 1
    if market_obj.error == '':
        irc(bitbot,'wdw > ' + market + ' >  withdrawal processed: ' + str(amount) + ' BTC to ' + str(address))
    else:
        irc(bitbot,'wdw > ' + market + ' > ' + market_obj.error)
            
withdraw.commands = ['withdraw','wdw']
withdraw.name = 'withdraw'

def lag(bitbot, input, output=True):
    markets = which(input,lag.commands)
    if output: 
        irc(bitbot,'lag > Getting lag from ' + ', '.join(markets) + ':')  
        
        for market in markets:
            error, market_obj = load(market)                            # load the correct market object
            if error == 0:                                              # market was loaded without errors
                market_obj.get_lag()                                    # execute the relevant function          
            elif error == 1:                                            # an error occured
                irc(bitbot,'lag > ' + market + ' > ' + market_obj)
                return 1
            if market_obj.error == '':
                irc(bitbot,'lag > ' + market + ' > ' + unicode(round(market_obj.lag, 3)) + ' seconds')
            else:
                irc(bitbot,'lag > ' + market + ' > error: ' + str(market_obj.error))
    else:
        market = markets[0]
        error, market_obj = load(market)
        if error == 0:
            market_obj.get_lag()
            return market_obj.lag
        else:
            return 'error fetching lag'

lag.commands = ['lag']
lag.name = 'lag'

def deal(bitbot, input, deals=None, manual_run=False):
    verify = {}
    deal_index = 1
    # Allow deals object to be passed in by outside function (e.g., TraderBot)
    if not deals:
        manual_run = True
        arbitrer = bitbot.variables.get('arbitrer')
        if arbitrer: # .arb is running and .deal is called manually
            arbitrer.deals = []     # Clear out old deals
            arbitrer.get_arb(bitbot)
            deals = arbitrer.deals
            for deal in arbitrer.deals:
                deal['index'] = deal_index
                deal_output = '{7} => {6:.2f}% | ${0:.2f} | {1:.2f} BTC | {2:11} ${3:.3f} => ${4:.3f} {5:11}'.format(\
                    deal['profit'], deal['purchase_volume'], deal['buy_market'], deal['buy_price'], deal['sell_price'], deal['sell_market'], deal['percent_profit'], deal_index)
                verify[deal_index] = [deal['buy_market'], deal['sell_market']]
                irc(bitbot, deal_output)
                deal_index += 1
        else: # .arb is not running and .deal is called manually
            bitbot.say('Setting up single-use instance...')
            arbitrer = arbitrage.Arbitrer(suppress_observers=True)
            arbitrer.get_arb(bitbot)
            deals = arbitrer.deals
            for deal in deals:
                deal_output = '{7} => {6:.2f}% | ${0:.2f} | {1:.2f} BTC | {2:11} ${3:.3f} => ${4:.3f} {5:11}'.format(\
                    deal['profit'], deal['purchase_volume'], deal['buy_market'], deal['buy_price'], deal['sell_price'], deal['sell_market'], deal['percent_profit'], deal_index)
                deal['index'] = deal_index
                verify[deal_index] = [deal['buy_market'], deal['sell_market']]
                irc(bitbot, deal_output)
                deal_index += 1
    elif deals: # .arb is running and .deal is called by traderbot
        arbitrer = bitbot.variables.get('arbitrer')

    if deals == []:
        irc(bitbot,'deal > error: no deals possible at this time')  
        return
    
    # Proceed if a deal is specified 
    parameters = input.split(' ')[1:]
    if len(parameters) != 1:
        irc(bitbot,'deal > usage: .deal #')
        bitbot.variables['verify'] = verify # Save the deals in a bot variable
        return
    else:       
        i = int(parameters[0]) - 1 
    
    # Formatting variables
    verify = bitbot.variables.get('verify') # Load the deals from a previous deal command
    if verify:
        try:
            if verify[i+1][0] != deals[i]['buy_market'] \
                or verify[i+1][1] != deals[i]['sell_market']:
                irc(bitbot,'deal > error: deal changed')
                return
        except IndexError:
            irc(bitbot, 'deal > error: deal not in range')
    
    irc(bitbot,'deal > verified')

    names = dict([(v.lower(),k) for k,v in config.private_markets.items()])
    buy_market = names[deals[i]['buy_market'][:-3].lower()]
    sell_market = names[deals[i]['sell_market'][:-3].lower()]
    
    volume = round(float(deals[i]['purchase_volume']),3)
    buy_price = round(float(deals[i]['buy_price']),2)
    buy_volume = round(volume*buy_price,2)
    sell_price = round(float(deals[i]['sell_price']),2)
    
    profit = round(float(deals[i]['profit']),2)
    percent_profit = round(float(deals[i]['percent_profit']),2)

    # Check to see if deals was passed to function to determine origin of call (irc input or from traderbot)                
    if manual_run:
        # Control the amount of USD in the buy market
        usd1, btc1 = balance(bitbot, '.bal ' + buy_market,False)
        if buy_volume <= usd1:
            buy_check = True
            irc(bitbot,'deal > ' + buy_market + ' > enough USD available for this deal ('  + str(buy_volume) + ' USD needed)')
        else:
            buy_check = False
            irc(bitbot,'deal > ' + buy_market + ' > error: not enough USD available to buy ('  + str(buy_volume) + ' USD needed)')
        
        # Control the funds in the sell market 
        usd2, btc2 = balance(bitbot, '.bal ' + sell_market,False)
        if volume <= btc2:
            sell_check = True
            irc(bitbot,'deal > ' + sell_market + ' > enough BTC available for this deal (' + str(volume) + ' BTC needed)')
        else:
            sell_check = False
            irc(bitbot,'deal > ' + sell_market + ' > error: not enough BTC available to sell (' + str(volume) + ' BTC needed)')
            
        # Stop the deal if there are not enough funds
        if not buy_check or not sell_check:
            irc(bitbot,'deal > insufficient funds')
            return
        else:    
            irc(bitbot,'deal > started, expected profit is $' + str(profit) + ' (' + str(percent_profit) + '%)') 
    
    # Executing trade orders
    irc(bitbot,'deal > .buy {} {} {}'.format(buy_market, volume, buy_price))
    buy(bitbot, '.buy {} {} {}'.format(buy_market, volume, buy_price))
    irc(bitbot,'deal > .sell {} {} {}'.format(sell_market, volume, sell_price))
    sell(bitbot, '.sell {} {} {}'.format(sell_market, volume, sell_price))

    # Execute BTC transfer from buy_market -> sell_market
    address = deposit(bitbot, '.dep ' + sell_market,False)
    irc(bitbot,'deal > .wdw {} {} {}'.format(buy_market, volume, address))
    withdraw(bitbot, '.wdw {} {} {}'.format(buy_market, volume, address),False)    
            
deal.commands = ['deal']
deal.name = 'deal'

if __name__ == '__main__':
    print __doc__.strip()

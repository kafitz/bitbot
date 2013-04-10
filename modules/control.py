#!/usr/bin/env python
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

import arbitrage          # arbitrage script
import config             # read the config file
import private_markets    # load private APIs
from decimal import Decimal

def irc(bitbot, msg, output=True):
    if output:
        bitbot.say(msg)
    else:
        print msg

def start_arbitrage(bitbot, input):
    if bitbot.variables.get('arb') is True:
        bitbot.say('arb > already running')
    else:
        bitbot.variables['arb'] = True
        irc(bitbot,'arb > starting up...')
        arbitrer = arbitrage.Arbitrer()
        while True:
            arbitrer.loop(bitbot)
        bitbot.say('Arbitrage quitting...')
        bitbot.variables['arb'] = False
        
start_arbitrage.commands = ['arb','arbitrage']
start_arbitrage.name = 'start_arbitrage'

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

def balance(bitbot, input, output=True):
    markets = which(input,balance.commands) 
    irc(bitbot,'bal > Getting balance from ' + ', '.join(markets) + ':',output)  
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.get_info()               # execute the relevant function
        elif error == 1:                        # an error occured
            irc(bitbot,'bal > ' + market + ' > ' + market_obj)
            return 0

        if market_obj.error == '':
            usd = float(market_obj.usd_balance)
            btc = float(market_obj.btc_balance)
            irc(bitbot,'bal > ' + market + ' > USD: {0:7} | BTC: {1:7} | Fee: {2}' \
                .format(str(round(usd, 3)), str(round(btc, 3)), round(float(market_obj.fee),2)))
            if not output:
                return usd, btc
        else:
            irc(bitbot,'bal > ' + market + ' > ' + market_obj.error)
            
            
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


def open_orders(bitbot, input, output=True):
    markets = which(input,open_orders.commands)
    irc(bitbot,'open > Getting open orders from ' + ', '.join(markets) + ':',output)
    orders = {}
    for market in markets:
        error, market_obj = load(market)        # load the correct market object
        if error == 0:                          # market was loaded without errors
            market_obj.get_orders()             # execute the relevant function
        elif error == 1:                        # an error occured
            irc(bitbot,'open > ' + market + ' > ' + market_obj)
            return 0

        if market_obj.error == '':
            for order in market_obj.orders_list:
                # Attempt to deal with unicode issues from difference encodings at different exchanges
                order_string = 'open > ' + market + u' > ' + order['timestamp'] + u': ' + order['type'] + u' ' +\
                    order['amount'] + u' for ' + order['price'] + u' [' + order['id'] + ']'
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
        irc(bitbot,'cancel > ' + market + ' > ' + market_obj.cancelled_time + ': cancelled ' + market_obj.cancelled_amount + ' [' + market_obj.cancelled_id + '] ')
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
        irc(bitbot,'buy > ' + market + ' > ' + market_obj.timestamp + ': bid ' + str(market_obj.amount) + ' BTC for ' +\
            str(market_obj.price) + ' USD/BTC placed [' + market_obj.id + ']')  
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
            irc(bitbot,'dep > ' + market + ' > address: ' + 'https://blockchain.info/address/' + market_obj.address + ' ' + market_obj.address)
            return market_obj.address
        else:
            irc(bitbot,'dep > ' + market + ' > error: ' + market_obj.error) 

            
deposit.commands = ['deposit','dep']
deposit.name = 'deposit'     

            
def withdraw(bitbot, input, output=True):
    # Test input formatting
    parameters = input.split(' ')[1:]
    if len(parameters) != 3:
        irc(bitbot,'wdw > invalid # of arguments specified: .wdw exchange amount address',output)
        return
    market = parameters[0]
    amount = parameters[1]
    address = parameters[2]
    
    error, market_obj = load(market)                            # load the correct market object
    if error == 0:                                              # market was loaded without errors
        market_obj.withdraw(amount, address)                    # execute the relevant function          
    elif error == 1:                                            # an error occured
        irc(bitbot,'wdw > ' + market + ' > ' + market_obj)
        return 1
    if market_obj.error == '':
        irc(bitbot,'wdw > ' + market + ' > ' + market_obj.timestamp + ': withdrawal processed')
    else:
        irc(bitbot,'wdw > ' + market + ' > ' + market_obj.error)
            
withdraw.commands = ['withdraw','wdw']
withdraw.name = 'withdraw'

def lag(bitbot, input, output=True):
    markets = which(input,lag.commands) 
    irc(bitbot,'lag > Getting lag from ' + ', '.join(markets) + ':')  
    
    for market in markets:
        error, market_obj = load(market)                            # load the correct market object
        if error == 0:                                              # market was loaded without errors
            market_obj.get_lag()                     # execute the relevant function          
        elif error == 1:                                            # an error occured
            irc(bitbot,'lag > ' + market + ' > ' + market_obj)
            return 1
        if market_obj.error == '':
            irc(bitbot,'lag > ' + market + ' > ' + market_obj.lag)
        else:
            irc(bitbot,'lag > ' + market + ' > error: ' + market_obj.error)
            
lag.commands = ['lag']
lag.name = 'lag'

def deal(bitbot, input, deals=None):
    # Allow deals object to be passed in by outside function (e.g., TraderBot)
    if not deals:
        arbitrer = arbitrage.Arbitrer()
        deals = arbitrer.get_arb(bitbot)
    #if no deal: deals = [{'sell_market': 'bitfloorUSD', 'purchase_volume': 0.42741999999999997, 'profit': 0.6566218314655998, 'buy_market': 'MtGoxUSD', 'percent_profit': 1.1427280663296235, 'buy_price': 133.63, 'sell_price': 136.5189404651163},{'sell_market': 'bitfloorUSD', 'purchase_volume': 0.42741999999999997, 'profit': 0.2855649263999993, 'buy_market': 'MtGoxUSD', 'percent_profit': 0.4956042046893483, 'buy_price': 133.99896, 'sell_price': 136.02}]
    names = dict([(v.lower(),k) for k,v in config.private_markets.items()])
    
    if deals == []:
        irc(bitbot,'deal > error: no deals possible at this time')  
        return
        
    deal_index = 1
    for deal in deals:
        deal_output = '{7} => {6:.2f}% | ${0:.2f} | {1:.2f} BTC | {2:11} ${3:.3f} => ${4:.3f} {5:11}'.format(\
            deal['profit'], deal['purchase_volume'], deal['buy_market'], deal['buy_price'], deal['sell_price'], deal['sell_market'], deal['percent_profit'], deal_index)
        irc(bitbot,deal_output)
        deal_index += 1
    
    # Proceed if a deal is specified 
    parameters = input.split(' ')[1:]
    if len(parameters) != 1:
        irc(bitbot,'deal > error: specify deal number')
        return 
    else:       
        i = int(parameters[0]) - 1 
    
    # Formatting variables
    buy_market = names[deals[i]['buy_market'][:-3].lower()]
    sell_market = names[deals[i]['sell_market'][:-3].lower()]
    
    volume = round(float(deals[i]['purchase_volume']),3)
    buy_price = round(float(deals[i]['buy_price']),2)
    buy_volume = round(volume*buy_price,2)
    sell_price = round(float(deals[i]['sell_price']),2)
    
    profit = round(float(deals[i]['profit']),2)
    percent_profit = round(float(deals[i]['percent_profit']),2)
            
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

def stats(bitbot, input, output=True):
    import sqlite3
    import datetime
    db = 'opportunties_database.db'
    conn = sqlite3.connect(db) 
    cursor = conn.cursor()  
    l = []
    markets = ['mtgoxusd','bitstampusd','bitfloorusd']
    for bm in markets:
        for sm in markets:
            d = {}
            d['buy market'], d['sell market'] = bm, sm
            cursor.execute("SELECT COUNT(*),AVG(profit), AVG(ratio), MAX(profit), MAX(ratio), MAX(time) FROM deals WHERE lower(sell_market)=? AND lower(buy_market)=?",[sm,bm])
            d['deals'], d['avg profit'], d['avg ratio'], d['max profit'], d['max ratio'], d['timestring']  = cursor.fetchone()
            if d['timestring'] != None:
                d['time'] = datetime.datetime.strptime(d['timestring'], "%Y-%m-%d %H:%M:%S")
                d['timedelta'] =datetime.datetime.utcnow() - d['time']
                d['timedeltastring'] = str(d['timedelta'].days) + ' days, ' + str(d['timedelta'].seconds/3600) + ' hours'
            l.append(d)
    irc(bitbot,'{0:11} => {1:11} | {2:4} | {3:5} | {4:5} | {5:5} | {6:5} | {7}'\
           .format('buy market','sell market','#','avg $', 'max $', 'avg %', 'max %', 'happened for the last time'))
    for d in l:
        if d['deals'] != 0:
            irc(bitbot,'{0:11} => {1:11} | {2:4} | {3:.3f} | {4:.3f} | {5:.3f} | {6:.3f} | {7} ago'\
                   .format(d['buy market'],d['sell market'],d['deals'],d['avg profit'],d['max profit'],d['avg ratio'],d['max ratio'],d['timedeltastring']))
    return
    
stats.commands = ['stats']
stats.name = 'stats'

if __name__ == '__main__':
    print __doc__.strip()

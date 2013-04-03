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
            usd = float(market_obj.usd_balance)
            btc = float(market_obj.btc_balance)
            bitbot.say('bal > ' + market + ' > USD: {0:7} | BTC: {1:7}'.format(str(round(usd, 3)), str(round(btc, 3))))
            return usd, btc
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
        bitbot.say('buy > ' + market + ' > ' + market_obj.timestamp + ': bid ' + str(market_obj.amount) + ' BTC for ' +\
            str(market_obj.price) + ' USD/BTC placed [' + market_obj.id + ']')  
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
            bitbot.say('dep > ' + market + ' > https://blockchain.info/address/' + market_obj.address)
            return market_obj.address
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
        return True
    else:
        bitbot.say('wdw > ' + market + ' > ' + market_obj.error)
            
withdraw.commands = ['withdraw','wdw']
withdraw.name = 'withdraw'

def deal(bitbot, input):
    arbitrer = arbitrage.Arbitrer()
    deals = arbitrer.get_arb(bitbot)
<<<<<<< HEAD
    deals = [{'sell_market': 'bitfloorUSD', 'purchase_volume': 0.42741999999999997, 'profit': 0.6566218314655998, 'buy_market': 'MtGoxUSD', 'percent_profit': 1.1427280663296235, 'buy_price': 133.63, 'sell_price': 136.5189404651163},{'sell_market': 'bitfloorUSD', 'purchase_volume': 0.42741999999999997, 'profit': 0.2855649263999993, 'buy_market': 'MtGoxUSD', 'percent_profit': 0.4956042046893483, 'buy_price': 133.99896, 'sell_price': 136.02}]
=======
    #if no deal: deals = [{'sell_market': 'bitfloorUSD', 'purchase_volume': 0.42741999999999997, 'profit': 0.6566218314655998, 'buy_market': 'MtGoxUSD', 'percent_profit': 1.1427280663296235, 'buy_price': 133.63, 'sell_price': 136.5189404651163},{'sell_market': 'bitfloorUSD', 'purchase_volume': 0.42741999999999997, 'profit': 0.2855649263999993, 'buy_market': 'MtGoxUSD', 'percent_profit': 0.4956042046893483, 'buy_price': 133.99896, 'sell_price': 136.02}]
>>>>>>> Recommented no-deal test line
    names = dict([(v.lower(),k) for k,v in config.private_markets.items()])
    
    if deals == []:
        bitbot.say('no deals possible at this time')  
        return
        
    deal_index = 1
    for deal in deals:
        deal_output = str(deal_index) + ". " + str(deal["profit"]) + " | " + deal["buy_market"] +\
            "  " + str(deal["buy_price"]) + " => " + str(deal["sell_price"]) + "  " + deal["sell_market"] + " | " +\
            str(deal["percent_profit"])
        bitbot.say(deal_output)
        deal_index += 1
        
    parameters = input.split(' ')[1:]
    if len(parameters) != 1:
        bitbot.say('deal > specify the deal number')
        return
         
    i = int(parameters[0]) - 1 
 
    buy_market = names[deals[i]['buy_market'][:-3].lower()]
    sell_market = names[deals[i]['sell_market'][:-3].lower()]
    
    volume = round(float(deals[i]['purchase_volume']),3)
    buy_price = round(float(deals[i]['buy_price']),2)
    buy_volume = round(volume*buy_price,2)
    sell_price = round(float(deals[i]['sell_price']),2)
    
    profit = round(float(deals[i]['profit']),2)
    percent_profit = round(float(deals[i]['percent_profit']),2)
            
    # Control the amount of USD in the buy market
    usd1, btc1 = balance(bitbot, '.bal ' + buy_market)
    if buy_volume <= usd1:
        buy_check = True
        bitbot.say('deal > ' + buy_market + ' > enough USD available for this deal ('  + str(buy_volume) + ' USD needed)')
    else:
        buy_check = False
        bitbot.say('deal > ' + buy_market + ' > error: not enough USD available to buy ('  + str(buy_volume) + '  USD needed)')
    
    # Control the funds in the sell market 
    usd2, btc2 = balance(bitbot, '.bal ' + sell_market)
    if volume <= btc2:
        sell_check = True
        bitbot.say('deal > ' + sell_market + ' > enough BTC available for this deal (' + str(volume) + ' BTC needed)')
    else:
        sell_check = False
        bitbot.say('deal > ' + sell_market + ' > error: not enough BTC available to sell (' + str(volume) + ' BTC needed)')
    
    if not buy_check or not sell_check:
        bitbot.say('deal > insufficient funds')
        return
        
    bitbot.say('deal > started, expected profit is $' + str(profit) + ' (' + str(percent_profit) + '%)') 
       
    bitbot.say('deal > QUITTING: test mode')
    return
    
    bitbot.say('deal > .buy {} {} {}'.format(buy_market, volume, buy_price))
    #buy(bitbot, '.buy {} {} {}'.format(buy_market, volume, buy_price))
    bitbot.say('deal > .sell {} {} {}'.format(sell_market, volume, sell_price))
    #sell(bitbot, '.sell {} {} {}'.format(sell_market, volume, buy_price))
    '''
    address = deposit(bitbot, '.dep ' + sell_market)
    bitbot.say('deal > .wdw {} {} {}'.format(buy_market, volume, address))
    withdraw(bitbot, ' '.join(['.wdw', buy_market, str(0), address]))
    '''
    
            
deal.commands = ['deal']
deal.name = 'deal'

if __name__ == '__main__':
    print __doc__.strip()

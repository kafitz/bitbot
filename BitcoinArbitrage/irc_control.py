'''IRC module for checking balances of exhanges in "private_markets" using their assigned initials.
	Ex: 'python balance.py mtgx' for Mt.Gox'''
import sys
import private_markets
import config

def get_balance(input_initials):
	private_market_names = config.private_markets
	for market in private_market_names:
		exec('import private_markets.' + market.lower())
		market = eval('private_markets.' + str(market.lower()) + '.Private' + str(market) + '()')
		if market.initials == input_initials:
			market.get_info() # Update class variables
			return market # Execute __str__ class of private market

def buy_btc():
	private_market_names = config.private_markets
	for market in private_market_names:
		exec('import private_markets.' + market.lower())
		market = eval('private_markets.' + str(market.lower()) + '.Private' + str(market) + '()')
		if market.initials == input_initials:
			pass

def sell_btc():
	private_market_names = config.private_markets
	for market in private_market_names:
		exec('import private_markets.' + market.lower())
		market = eval('private_markets.' + str(market.lower()) + '.Private' + str(market) + '()')
		if market.initials == input_initials:
			pass
			
def open_orders(input_initials):
	private_market_names = config.private_markets
	for market in private_market_names:
		exec('import private_markets.' + market.lower())
		market = eval('private_markets.' + str(market.lower()) + '.Private' + str(market) + '()')
		if market.initials == input_initials:
			market.get_orders()
			return market

def transactions(input_initials):
	private_market_names = config.private_markets
	for market in private_market_names:
		exec('import private_markets.' + market.lower())
		market = eval('private_markets.' + str(market.lower()) + '.Private' + str(market) + '()')
		if market.initials == input_initials:
			market.get_txs()
			return market
			
if __name__ == "__main__":
	command = sys.argv[1]
	input_market = sys.argv[2]
	if command in ['balance', 'bal']:
		get_balance(input_market)
		pass
	if command in ['buy']:
		buy_btc()
	if command in ['sell']:
		sell_btc()
	# Seems super dangerous if we enter the wrong address while in dev
	# if command in ['withdraw']:
	# 	pass

#!/usr/bin/env python
"""
btc-arbitrage module
Kyle Fitzsimmons 2013, http://kylefitz.com/
"""

from BitcoinArbitrage import arbitrage

def arb(bitbot, input):
    bitbot.say("Starting up btc-arbitrage...")
    arbitrer = arbitrage.Arbitrer()
    while True:
        arbitrer.loop(bitbot)
arb.commands = ['arb']
arb.name = 'arb'


if __name__ == "__main__":
    print __doc__.strip()

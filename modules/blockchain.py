#!/usr/bin/env python
'''
module to query the blockchain.info API from IRC

Kyle Fitzsimmons 2013, http://kylefitz.com/
Bas Pennewaert 2013, bas@pennewaert.com

'''
import json
import requests
import urllib
from decimal import Decimal

def from_int_amount(amount):
    return Decimal(amount) / Decimal(100000000.)

def send_request(path):
    base = 'http://blockchain.info/'
    url = base + path + '?format=json'
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
    except requests.exceptions.Timeout:
        print "Request to " + self.name + " timed out."
        error = "request timed out"
        print error
        return
    except requests.exceptions.SSLError, e:
        print e
        print "SSL Error: check server certificate to " + self.name
        error = "SSL certificate mismatch"
        print error
        return
    if response.status_code == 200:
        jsonstr = json.loads(response.text)
        return jsonstr
    return 0
    
def blockchain(bitbot, input):
    if input[1:] in blockchain.commands:
        bitbot.say('bc > usage: .bc address')
        return 0
    else: 
        address = input.split(' ', 1)[1]
        if len(address) != 34:
            bitbot.say('bc > error: invalid address')
            return 0 
    
    response = send_request('address/' + address)
    if response:
        total_sent = str(round(from_int_amount(response['total_sent']),3))
        total_received = str(round(from_int_amount(response['total_received']),3))
        final_balance = str(round(from_int_amount(response['final_balance']),3))
        n_tx = str(response['n_tx'])  
        bitbot.say('bc > sent: {} BTC | received: {} BTC | balance: {}  BTC | txs: {}'\
                    .format(total_sent, total_received, final_balance, n_tx))
    return
    
blockchain.commands = ['blockchain','bc','block']
blockchain.name = 'blockchain'

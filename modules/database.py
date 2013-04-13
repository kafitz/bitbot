#!/usr/bin/env python
'''
module to query the sqlite3 database from IRC

Kyle Fitzsimmons 2013, http://kylefitz.com/
Bas Pennewaert 2013, bas@pennewaert.com

'''

import sqlite3
import datetime
import config
        
def dbstats(bitbot, input):
    db = 'opportunties_database.db'
    conn = sqlite3.connect(db) 
    cursor = conn.cursor()  
    l = []
    markets = ['mtgoxusd','bitstampusd','bitfloorusd','campbxusd']
    for bm in markets:
        for sm in markets:
            d = {}
            d['buy market'], d['sell market'] = bm, sm
            cursor.execute("SELECT COUNT(*),AVG(profit), AVG(ratio), MAX(time) FROM deals WHERE lower(sell_market)=? AND lower(buy_market)=?",[sm,bm])
            d['deals'], d['avg profit'], d['avg ratio'], d['timestring']  = cursor.fetchone()
            if d['timestring'] != None:
                d['time'] = datetime.datetime.strptime(d['timestring'], "%Y-%m-%d %H:%M:%S")
                d['timedelta'] =datetime.datetime.utcnow() - d['time']
                if d['timedelta'].days != 0:
                    d['timedeltastring'] = str(d['timedelta'].days) + ' days ago'
                elif d['timedelta'].seconds/3600 != 0:
                    d['timedeltastring'] = str(d['timedelta'].seconds/3600) + ' hours ago'
                elif d['timedelta'].seconds/60 != 0:
                    d['timedeltastring'] = str(d['timedelta'].seconds/60) + ' minutes ago'
                else:
                    d['timedeltastring'] = 'just now'
                    print d['timedelta'].seconds
            l.append(d)
    bitbot.say('{0:8} => {1:8} | {2:4} | {3:6} | {4:6} | {5}'\
           .format('buy','sell','#','avg $', 'avg %', 'happened for the last time'))
    for d in l:
        if d['deals'] != 0:
            bitbot.say('{0:8} => {1:8} | {2:4} | {3:6} | {4:6} | {5} ago'\
                   .format(d['buy market'][:-3],d['sell market'][:-3],d['deals'],
                           str(round(d['avg profit'],3)),str(round(d['avg ratio'],3)),d['timedeltastring']))
    return
    
dbstats.commands = ['dbstats']
dbstats.name = 'dbstats'

if __name__ == '__main__':
    print __doc__.strip()

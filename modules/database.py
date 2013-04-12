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
            cursor.execute("SELECT COUNT(*),AVG(profit), AVG(ratio), MAX(profit), MAX(ratio), MAX(time) FROM deals WHERE lower(sell_market)=? AND lower(buy_market)=?",[sm,bm])
            d['deals'], d['avg profit'], d['avg ratio'], d['max profit'], d['max ratio'], d['timestring']  = cursor.fetchone()
            if d['timestring'] != None:
                d['time'] = datetime.datetime.strptime(d['timestring'], "%Y-%m-%d %H:%M:%S")
                d['timedelta'] =datetime.datetime.utcnow() - d['time']
                d['timedeltastring'] = str(d['timedelta'].days) + ' days, ' + str(d['timedelta'].seconds/3600) + ' hours'
            l.append(d)
    bitbot.say('{0:11} => {1:11} | {2:4} | {3:5} | {4:5} | {5:5} | {6:5} | {7}'\
           .format('buy market','sell market','#','avg $', 'max $', 'avg %', 'max %', 'happened for the last time'))
    for d in l:
        if d['deals'] != 0:
            bitbot.say('{0:11} => {1:11} | {2:4} | {3:.3f} | {4:.3f} | {5:.3f} | {6:.3f} | {7} ago'\
                   .format(d['buy market'],d['sell market'],d['deals'],d['avg profit'],d['max profit'],d['avg ratio'],d['max ratio'],d['timedeltastring']))
    return
    
dbstats.commands = ['dbstats']
dbstats.name = 'dbstats'

if __name__ == '__main__':
    print __doc__.strip()

#!/usr/bin/env python

import threading, time

def setup(bitbot): 
   # by clsn
   bitbot.data = {}
   refresh_delay = 300.0

   if hasattr(bitbot.config, 'refresh_delay'):
      try: refresh_delay = float(bitbot.config.refresh_delay)
      except: pass

      def close():
         print "Nobody PONGed our PING, restarting"
         bitbot.handle_close()
      
      def pingloop():
         timer = threading.Timer(refresh_delay, close, ())
         bitbot.data['startup.setup.timer'] = timer
         bitbot.data['startup.setup.timer'].start()
         # print "PING!"
         bitbot.write(('PING', bitbot.config.host))
      bitbot.data['startup.setup.pingloop'] = pingloop

      def pong(bitbot, input):
         try:
            # print "PONG!"
            bitbot.data['startup.setup.timer'].cancel()
            time.sleep(refresh_delay + 60.0)
            pingloop()
         except: pass
      pong.event = 'PONG'
      pong.thread = True
      pong.rule = r'.*'
      bitbot.variables['pong'] = pong

      # Need to wrap handle_connect to start the loop.
      inner_handle_connect = bitbot.handle_connect

      def outer_handle_connect():
         inner_handle_connect()
         if bitbot.data.get('startup.setup.pingloop'):
            bitbot.data['startup.setup.pingloop']()

      bitbot.handle_connect = outer_handle_connect

def startup(bitbot, input): 
   import time

   if hasattr(bitbot.config, 'serverpass'): 
      bitbot.write(('PASS', bitbot.config.serverpass))

   if hasattr(bitbot.config, 'password'): 
      bitbot.msg('NickServ', 'IDENTIFY %s' % bitbot.config.password)
      time.sleep(5)

   # Cf. http://swhack.com/logs/2005-12-05#T19-32-36
   for channel in bitbot.channels: 
      bitbot.write(('JOIN', channel))
      time.sleep(0.5)
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'

if __name__ == '__main__': 
   print __doc__.strip()

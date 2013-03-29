#!/usr/bin/env python

def deprecated(old): 
   def new(bitbot, input, old=old): 
      self = bitbot
      origin = type('Origin', (object,), {
         'sender': input.sender, 
         'nick': input.nick
      })()
      match = input.match
      args = [input.bytes, input.sender, '@@']

      old(self, origin, match, args)
   new.__module__ = old.__module__
   new.__name__ = old.__name__
   return new

if __name__ == '__main__': 
   print __doc__.strip()

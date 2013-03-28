#!/usr/bin/env python

import sys, os.path, time, imp
import irc

def f_reload(bitbot, input): 
   """Reloads a module, for use by admins only.""" 
   if not input.admin: return

   name = input.group(2)
   if name == bitbot.config.owner: 
      return bitbot.reply('What?')

   if (not name) or (name == '*'): 
      bitbot.variables = None
      bitbot.commands = None
      bitbot.setup()
      return bitbot.reply('done')

   if not sys.modules.has_key(name): 
      return bitbot.reply('%s: no such module!' % name)

   # Thanks to moot for prodding me on this
   path = sys.modules[name].__file__
   if path.endswith('.pyc') or path.endswith('.pyo'): 
      path = path[:-1]
   if not os.path.isfile(path): 
      return bitbot.reply('Found %s, but not the source file' % name)

   module = imp.load_source(name, path)
   sys.modules[name] = module
   if hasattr(module, 'setup'): 
      module.setup(bitbot)

   mtime = os.path.getmtime(module.__file__)
   modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

   bitbot.register(vars(module))
   bitbot.bind_commands()

   bitbot.reply('%r (version: %s)' % (module, modified))
f_reload.name = 'reload'
f_reload.rule = ('$nick', ['reload'], r'(\S+)?')
f_reload.priority = 'low'
f_reload.thread = False

if __name__ == '__main__': 
   print __doc__.strip()

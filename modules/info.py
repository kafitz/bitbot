#!/usr/bin/env python

def doc(bitbot, input): 
   """Shows a command's documentation, and possibly an example."""
   name = input.group(1)
   name = name.lower()

   if bitbot.doc.has_key(name): 
      bitbot.reply(bitbot.doc[name][0])
      if bitbot.doc[name][1]: 
         bitbot.say('e.g., ' + bitbot.doc[name][1])
doc.rule = ('$nick', '(?i)(?:help|doc) +([A-Za-z]+)(?:\?+)?$')
doc.example = '$nickname: doc tell?'
doc.priority = 'low'

def commands(bitbot, input): 
   # This function only works in private message
   if input.sender.startswith('#'): return
   names = ', '.join(sorted(bitbot.doc.iterkeys()))
   bitbot.say('Commands I recognise: ' + names + '.')
   bitbot.say(("For help, do '%s: help example?' where example is the " + 
               "name of the command you want help for.") % bitbot.nick)
commands.commands = ['commands']
commands.priority = 'low'

def help(bitbot, input): 
   response = (
      'Hi, I\'m a bot. Say ".commands" to me in private for a list ' + 
      'of my commands, or see http://inamidst.com/bitbot/ for more ' + 
      'general details. My owner is %s.'
   ) % bitbot.config.owner
   bitbot.reply(response)
help.rule = ('$nick', r'(?i)help(?:[?!]+)?$')
help.priority = 'low'

def stats(bitbot, input): 
   """Show information on command usage patterns."""
   commands = {}
   users = {}
   channels = {}

   ignore = set(['f_note', 'startup', 'message', 'noteuri'])
   for (name, user), count in bitbot.stats.items(): 
      if name in ignore: continue
      if not user: continue

      if not user.startswith('#'): 
         try: users[user] += count
         except KeyError: users[user] = count
      else: 
         try: commands[name] += count
         except KeyError: commands[name] = count

         try: channels[user] += count
         except KeyError: channels[user] = count

   comrank = sorted([(b, a) for (a, b) in commands.iteritems()], reverse=True)
   userank = sorted([(b, a) for (a, b) in users.iteritems()], reverse=True)
   charank = sorted([(b, a) for (a, b) in channels.iteritems()], reverse=True)

   # most heavily used commands
   creply = 'most used commands: '
   for count, command in comrank[:10]: 
      creply += '%s (%s), ' % (command, count)
   bitbot.say(creply.rstrip(', '))

   # most heavy users
   reply = 'power users: '
   for count, user in userank[:10]: 
      reply += '%s (%s), ' % (user, count)
   bitbot.say(reply.rstrip(', '))

   # most heavy channels
   chreply = 'power channels: '
   for count, channel in charank[:3]: 
      chreply += '%s (%s), ' % (channel, count)
   bitbot.say(chreply.rstrip(', '))
stats.commands = ['stats']
stats.priority = 'low'

if __name__ == '__main__': 
   print __doc__.strip()

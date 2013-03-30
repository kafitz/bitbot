bitbot
=============
(IRC instance of bitcoin-arbitrage) -- https://github.com/kafitz/btc-arbitrage <br />
These projects are primarily in sync, the only difference currently being with 'arbitrage.py'. Eventually
it will probably be desirable having a trader independent of the IRC platform as well so we can hook into
live trade quotes via web sockets (as an example).

Ideally the bitbot trades will be automated and can be controlled via irc. That means first off, we should 
probably adding a hard shutdown command from the IRC interface before we ever get to live trading mode.

The IRC bot is a stripped-down version of the Phenny/Jenni framework with its primarily module being the adapted version of btc-arbitrage. The project structure is as follows:

* bitbot - core IRC bot module used for creating config file and launching bot loop
* irc.py - phenny module for irc server-client interaction
* web.py - provides a web framework for various default phenny/jenni plugins, not yet sure if needed with stripped down version
* BeautifulSoup.py - used for providing unicode support for characters in page titles used by modules/url.py
* BitcoinArbitrage/ - version of btc-arbitrage customized to output to IRC via "yield" statements in get_ticker() loop
* modules/:
	* admin.py - provides control commands for bot through IRC
	* control.py - module to control the BitcoinArbitrage project from IRC
	* calc.py - google calc for math and currency conversion
	* info.py - help module
	* ping.py - unsure of necessity
	* reload.py - for live reloading of these modules
	* seen.py - keeps track of last time nick has been seen in channel
	* startup.py - looks to provide initialization commands to IRC server, possibly deprecated by core irc.py/bot.py?
	* tell.py - message service
	* url.py - announce page titles of pasted links

#!/usr/bin/env python

import urllib2
import re
import HTMLParser
from BeautifulSoup import BeautifulStoneSoup

def url_announce(bitbot, input):
    '''Watches irc channels for urls in what users say and posts page title'''
    h = HTMLParser.HTMLParser()
    url_pattern = re.compile(r'http(s?)://\S+')
    title_regex = re.compile('<title>(.*?)</title>', re.IGNORECASE|re.DOTALL)
    # Try regex match for each word in line
    word_list = input.bytes.split(" ")
    for word_string in word_list:
        url_match = re.match(url_pattern, word_string)
        if url_match:
            url = url_match.group()
            try: ## Follow page redirect if exists
                redirect_url = urllib2.urlopen(url).geturl()
                page_data = urllib2.urlopen(redirect_url).read()
                url = redirect_url
            except Exception, e:
                print e
            try: ## Fetch page url and say it to IRC channel
                title_html_str = title_regex.search(page_data).group(1)
                title_html = title_html_str.strip()
                # Convert HTML entities to unicode entities (for accented and special characters that lxml and HTML parser don't deal with)
                title_list = BeautifulStoneSoup(title_html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents
                page_title = title_list[0]
                # Only output page titles longer than 3 words long to cut down on obvious page names like "Google" for google.com
                if len(page_title.split(" ")) > 3:
                    # Add quotes to output string and convert HTML character codes to unicode w/ HTMLParser
                    irc_output = h.unescape('\"' + page_title + '\"')
                    bitbot.say(irc_output)
            except Exception, e:
                # print "No <title> tag exists in linked URL's html."
                pass
    return

url_announce.rule = r'(.*?)https?://'
url_announce.name = 'url_announce'
url_announce.example = 'ted: http://www.reuters.com --> irc_bot: "Breaking News, Top News & Latest News Headlines | Reuters.com"'
url_announce.priority = 'medium'


if __name__ == "__main__":
    print __doc__.strip()
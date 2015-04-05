import logging
logger = logging.getLogger('')

from os.path import exists
from urllib import urlopen
from bs4 import BeautifulSoup
from lxml import etree

from .tasks import async_http


class Scraper(object):
    def __init__(self, sync=False, cache=True):
        self.sync = sync
        self.cache = cache

    def get_with_nl(self, url, name):
        soup = self.get(url, name)
        suppe = self.get(url.replace("&language=fr", "&language=nl", 1), name + " nl")
        return soup, suppe


    def get(self, url, name):
        logger.debug("\033[0;33mparsing %s --- %s\033[0m" % (url, name))
        text = self.retreive_content(url, name)
        soup = BeautifulSoup(text, "html5lib", from_encoding="latin1")
        if soup.title.text == "404 Not Found":
            raise IndexError
        return soup


    def lxml_get_with_nl(self, url, name):
        soup = self.lxml_get(url, name)
        suppe = self.lxml_get(url.replace("&language=fr", "&language=nl", 1), name + " nl")
        return soup, suppe


    def lxml_get(self, url, name):
        logger.debug("LXML parsing %s --- %s" % (url, name))
        text = self.retreive_content(url)
        soup = etree.parse(text, etree.HTMLParser())
        return soup

    def retreive_content(self, url, key):
        if self.cache and exists('dump/%s' % key):
            return open('dump/%s' % key, "r").read()

        if self.sync:
            content = urlopen(url).read()
        else:
            content = async_http.delay(url).get()

        open('dump/%s' % key, "w").write(content)
        return content

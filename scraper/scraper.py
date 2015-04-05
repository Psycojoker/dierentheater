import logging
logger = logging.getLogger('')

from os.path import exists
from urllib import urlopen
from bs4 import BeautifulSoup
from lxml import etree

from django.conf import settings


class Scraper(object):
    def __init__(self, sync=False, cache=True):
        self.sync = sync
        self.cache = cache

    def get_with_nl(self, url, name, reset=False):
        soup = self.get(url, name, reset=reset)
        suppe = self.get(url.replace("&language=fr", "&language=nl", 1), name + " nl", reset=reset)
        return soup, suppe


    def get(self, url, name, reset=False):
        logger.debug("\033[0;33mparsing %s --- %s\033[0m" % (url, name))
        if not reset and exists('dump/%s' % name) and settings.CACHE_SCRAPING:
            text = open('dump/%s' % name).read()
        else:
            text = self.http(url)
            open('dump/%s' % name, "w").write(text)
        soup = BeautifulSoup(text, "html5lib", from_encoding="latin1")
        if soup.title.text == "404 Not Found":
            raise IndexError
        return soup


    def lxml_get_with_nl(self, url, name, reset=False):
        soup = self.lxml_get(url, name, reset)
        suppe = self.lxml_get(url.replace("&language=fr", "&language=nl", 1), name + " nl", reset)
        return soup, suppe


    def lxml_get(self, url, name, reset=False):
        logger.debug("LXML parsing %s --- %s" % (url, name))
        if not reset and exists('dump/%s' % name) and settings.CACHE_SCRAPING:
            text = open('dump/%s' % name)
        else:
            text = self.http(url)
            open('dump/%s' % name, "w").write(text)
        soup = etree.parse(text, etree.HTMLParser())
        return soup

    def http(self, url):
        return urlopen(url).read()

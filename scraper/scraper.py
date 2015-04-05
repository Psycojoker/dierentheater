import logging
logger = logging.getLogger('')

from os.path import exists
from urllib import urlopen
from bs4 import BeautifulSoup
from lxml import etree

from django.conf import settings


class Scraper(object):
    def __init__(self, sync=False):
        self.sync = sync

    def get_with_nl(self, url, name, reset=False):
        soup = self.read_or_dl(url, name, reset=reset)
        suppe = self.read_or_dl(url.replace("&language=fr", "&language=nl", 1), name + " nl", reset=reset)
        return soup, suppe


    def get(self, url, name, reset=False):
        logger.debug("\033[0;33mparsing %s --- %s\033[0m" % (url, name))
        if not reset and exists('dump/%s' % name) and settings.CACHE_SCRAPING:
            text = open('dump/%s' % name).read()
        else:
            text = urlopen(url).read()
            open('dump/%s' % name, "w").write(text)
        soup = BeautifulSoup(text, "html5lib", from_encoding="latin1")
        if soup.title.text == "404 Not Found":
            raise IndexError
        return soup


    def lxml_get_with_nl(self, url, name, reset=False):
        soup = self.lxml_read_or_dl(url, name, reset)
        suppe = self.lxml_read_or_dl(url.replace("&language=fr", "&language=nl", 1), name + " nl", reset)
        return soup, suppe


    def lxml_get(self, url, name, reset=False):
        logger.debug("LXML parsing %s --- %s" % (url, name))
        if not reset and exists('dump/%s' % name) and settings.CACHE_SCRAPING:
            text = open('dump/%s' % name)
        else:
            text = urlopen(url)
            open('dump/%s' % name, "w").write(urlopen(url).read())
        soup = etree.parse(text, etree.HTMLParser())
        return soup

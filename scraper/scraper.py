import logging
logger = logging.getLogger('')

from os.path import exists
from urllib import urlopen
from bs4 import BeautifulSoup
from lxml import etree

from .tasks import async_http


def get_with_nl(url, name, cache, sync):
    soup = get(url, name, cache=cache, sync=sync)
    suppe = get(url.replace("&language=fr", "&language=nl", 1), name + " nl", cache=cache, sync=sync)
    return soup, suppe


def get(url, name, cache, sync):
    logger.debug("\033[0;33mparsing %s --- %s\033[0m" % (url, name))
    text = retreive_content(url, name, cache=cache, sync=sync)
    soup = BeautifulSoup(text, "html5lib", from_encoding="latin1")
    if soup.title.text == "404 Not Found":
        raise IndexError
    return soup

def to_soup(html):
    return BeautifulSoup(html, "html5lib", from_encoding="latin1")


def lxml_get_with_nl(url, name, cache, sync):
    soup = lxml_get(url, name, cache=cache, sync=sync)
    suppe = lxml_get(url.replace("&language=fr", "&language=nl", 1), name + " nl", cache=cache, sync=sync)
    return soup, suppe


def lxml_get(url, name, cache, sync):
    logger.debug("LXML parsing %s --- %s" % (url, name))
    text = retreive_content(url, cache=cache, sync=sync)
    soup = etree.parse(text, etree.HTMLParser())
    return soup

def retreive_content(url, key, cache, sync):
    if cache and exists('dump/%s' % key):
        return open('dump/%s' % key, "r").read()

    if sync:
        content = urlopen(url).read()
    else:
        content = async_http.delay(url).get()

    open('dump/%s' % key, "w").write(content)
    return content

# -*- coding:Utf-8 -*-

#  Dieren Theater - lachambre.be to json sausage machine
#  Copyright (C) 2012  Laurent Peuch <cortex@worlddomination.be>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.


import re
import logging
logger = logging.getLogger('')
from os.path import exists
from urllib import urlopen, quote
from bs4 import BeautifulSoup
from lxml import etree

from django.conf import settings

from history.utils import irc


LACHAMBRE_PREFIX = "http://www.lachambre.be/kvvcr/"
DOSSIER_ID_REGEX = "dossierID=([0-9A-Za-z-]+).xml"


def get_or_create(klass, _id=None, **kwargs):
    if _id is None:
        object = klass.objects.filter(**kwargs)
    else:
        object = klass.objects.filter(**{_id: kwargs[_id]})
    if object:
        return object[0]
    else:
        logger.debug("\033[0;36madd new %s %s\033[0m" % (klass.__name__, kwargs))
        result = klass(**kwargs)
        result.save()
        return result


def update_or_create(klass, _id=None, **kwargs):
    if _id is None:
        object = klass.objects.filter(**kwargs)
    else:
        object = klass.objects.filter(**{_id: kwargs[_id]})
    if object:
        result = object[0]
        for key, value in kwargs.items():
            setattr(result, key, value)
        logger.debug("\033[0;36mupdate %s %s\033[0m" % (klass.__name__, kwargs))
    else:
        logger.debug("\033[0;32add new %s %s\033[0m" % (klass.__name__, kwargs))
        result = klass(**kwargs)

    result.save()
    return result


def retry_on_access_error(function):
    "decorator to retry to download a page because La Chambre website sucks"
    def wrap(*args, **kwargs):
        reset = False
        for i in xrange(4):
            try:
                return function(*args, reset=reset, **kwargs)
            except (IndexError, AttributeError, TypeError), e:
                logger.debug("%s" % e)
                reset = True
        logger.debug("WARNING, function keeps failling %s %s %s" % (function, args, kwargs))
    return wrap


def get_text_else_blank(dico, key):
    return dico[key].text if dico.get(key) and dico[key].a else ""


def get_href_else_blank(dico, key):
    return dico[key].a["href"] if dico.get(key) and dico[key].a else ""


def get_items_list_else_empty_list(dico, key):
    return dico[key].text.split(" | ") if dico.get(key) else []


def dico_get_text(dico, key):
    if dico.get(key):
        return dico[key].text
    return ""


class AccessControlDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.accessed = set()

    def __getitem__(self, key):
        self.accessed.add(key)
        return dict.__getitem__(self, key)

    def get_not_accessed_keys(self):
        a = []
        for i in self.keys():
            if i not in self.accessed:
                a.append(i)
            elif isinstance(self[i], AccessControlDict) and self[i].get_not_accessed_keys():
                a.append(i)
                a.append(self[i].get_not_accessed_keys())

        return a

    def die_if_got_not_accessed_keys(self):
        if self.get_not_accessed_keys():
            logger.error("\nError: untreated sections:")
            irc("\nError: untreated sections:")
            for i in self.get_not_accessed_keys():
                if isinstance(i, (str, unicode)):
                    logger.error("* %s" % i)
                    irc("* %s" % i.encode("Utf-8"))
                else:
                    for j in i:
                        logger.error("    * %s" % j)
                        irc("    * %s" % j.encode("Utf-8"))
            logger.error("------------ stop ------------")
            irc("Bram: Error: dico got un-accessed keys, die")
            import sys
            sys.exit(1)


def clean_text(text):
    def rep(result):
        string = result.group()                   # "&#xxx;"
        n = int(string[2:-1])
        uchar = unichr(n)                         # matching unicode char
        return uchar

    return re.sub("(\r|\t|\n| )+", " ", re.sub("&#\d+;", rep, text)).strip()


def lame_url(url):
    # convert super lame urls of lachambre.be into something uzable
    return quote(url.encode("iso-8859-1"), safe="%/:=&?~#+!$,;'@()*[]")


def read_or_dl_with_nl(url, name, reset=False):
    soup = read_or_dl(url, name, reset=reset)
    suppe = read_or_dl(url.replace("&language=fr", "&language=nl", 1), name + " nl", reset=reset)
    return soup, suppe


def read_or_dl(url, name, reset=False):
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


def lxml_read_or_dl_with_nl(url, name, reset=False):
    soup = lxml_read_or_dl(url, name, reset)
    suppe = lxml_read_or_dl(url.replace("&language=fr", "&language=nl", 1), name + " nl", reset)
    return soup, suppe


def lxml_read_or_dl(url, name, reset=False):
    logger.debug("LXML parsing %s --- %s" % (url, name))
    if not reset and exists('dump/%s' % name) and settings.CACHE_SCRAPING:
        text = open('dump/%s' % name)
    else:
        text = urlopen(url)
        open('dump/%s' % name, "w").write(urlopen(url).read())
    soup = etree.parse(text, etree.HTMLParser())
    return soup


def table2dic(table):
    dico = {}
    for x, y in zip(table[::2], table[1::2]):
        dico[x.text] = y.text if y.a is None else y.a
    return dico


def document_pdf_part_cutter(soup):
    result = []
    blob = [soup('tr')[0]]
    for i in soup('tr')[1:]:
        if not clean_text(i.text):
            continue
        if not i.img or not i.img.get("class") or i.img["class"] != "picto":
            blob.append(i)
        else:
            result.append(blob)
            blob = [i]

    result.append(blob)
    return result


def document_to_dico(table):
    is_pdf_section = lambda i: i.td.img
    is_noise = lambda i: i == u"\n" or i.td.text in ("&#13;", "&nbsp;", "&#160;")
    is_subsection = lambda i: i.td.b
    dico = AccessControlDict()
    sub_section = None
    for i in table:
        if is_noise(i):
            continue
        if is_subsection(i):
            sub_section = _build_sub_section(i, dico)
        elif is_pdf_section(i):
            _build_pdf_sub_section(i, dico, sub_section)
        else:  # is first level
            _build_first_level(i, dico)
    return dico


def _build_sub_section(i, dico):
    sub_section = clean_text(i.td.b.text)
    if dico.get(sub_section):
        raise Exception("'%s' is already use as a key for '%s'" % (sub_section, dico[sub_section]))
    dico[sub_section] = AccessControlDict()
    dico[sub_section]["head"] = i('td')[1]
    return sub_section


def _build_pdf_sub_section(i, dico, sub_section):
    key = clean_text(i.td.text)
    # we can have a list on joined documents
    if unicode(key) in (u'Document(s) joint(s)/lié(s)', u'Gekoppeld(e)/verbonden document(en)'):
        if not dico[sub_section].get(key):
            dico[sub_section][key] = []
        dico[sub_section][key].append(i('td')[1])
    elif dico[sub_section].get(key):
        raise Exception("'%s' is already use as a key in the sub_section '%s' for '%s'" % (key, sub_section, dico[sub_section][key]))
    else:
        dico[sub_section][key] = i('td')[1]


def _build_first_level(i, dico):
    key = clean_text(i.td.text)
    # we can get severals Moniter erratum
    if unicode(key) in ('Moniteur erratum', 'Staatsblad erratum'):
        if not dico.get(key):
            dico[key] = []
        dico[key].append(i('td')[1])
    else:
        if dico.get(key):
            raise Exception("'%s' is already use as a key for '%s'" % (key, dico[key]))
        dico[key] = i('td')[1]


class Parsable(object):
    @classmethod
    def scrape(klass, only_new=False):
        if only_new:
            klass.fetch_new()
        else:
            klass.fetch_list()

    @classmethod
    def fetch_new(klass):
        klass.get_list()

    @classmethod
    def fetch_list(klass):
        raise NotImplementedError()

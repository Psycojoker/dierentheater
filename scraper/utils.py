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
from urllib import quote

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


def table2dic(table):
    dico = {}
    for x, y in zip(table[::2], table[1::2]):
        dico[x.text] = y.text if y.a is None else y.a
    return dico


class Parsable(object):
    @classmethod
    def scrape(klass, only_new=False, cache=False, sync=False):
        if only_new:
            klass.fetch_new(cache=cache, sync=sync)
        else:
            klass.fetch_list(cache=cache, sync=sync)

    @classmethod
    def fetch_new(klass):
        klass.get_list()

    @classmethod
    def fetch_list(klass):
        raise NotImplementedError()

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
from os.path import exists
from urllib import urlopen, quote
from BeautifulSoup import BeautifulSoup
from lxml import etree

LACHAMBRE_PREFIX = "http://www.lachambre.be/kvvcr/"


def get_or_create(klass, _id=None, **kwargs):
    if _id is None:
        object = klass.objects.filter(**kwargs)
    else:
        object = klass.objects.filter(**{_id: kwargs[_id]})
    if object:
        return object[0]
    else:
        print "add new", klass.__name__, kwargs
        return klass.objects.create(**kwargs)


def retry_on_access_error(function):
    "decorator to retry to download a page because La Chambre website sucks"
    def wrap(*args, **kwargs):
        reset = False
        for i in xrange(4):
            try:
                return function(*args, reset=reset, **kwargs)
            except (IndexError, AttributeError, TypeError), e:
                print e
                reset = True
        print "WARNING, function keeps failling", function, args, kwargs
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
            print "\nError: untreated sections:"
            for i in self.get_not_accessed_keys():
                if isinstance(i, (str, unicode)):
                    print "*", i
                else:
                    for j in i:
                        print "    *", j
            print "------------ stop ------------"
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
    print "parsing", url, "---", name
    if not reset and exists('dump/%s' % name):
        text = open('dump/%s' % name).read()
    else:
        text = urlopen(url).read()
        open('dump/%s' % name, "w").write(text)
    soup = BeautifulSoup(text)
    if soup.title.text == "404 Not Found":
        raise IndexError
    return soup


def lxml_read_or_dl(url, name, reset=False):
    print "LXML parsing", url, "---", name
    if not reset and exists('dump/%s' % name):
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

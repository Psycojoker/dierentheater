# -*- coding:Utf-8 -*-

#  Dieren Theater - lachambre.be to json sausage machine
#  Copyright (C) 2011  Laurent Peuch <cortex@worlddomination.be>
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

from deputies.models import Deputy, Party, CommissionMembership, Document, Question, Analysis, Commission

LACHAMBRE_PREFIX="http://www.lachambre.be/kvvcr/"

def hammer_time(function):
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

def lame_url(url):
    # convert super lame urls of lachambre.be into something uzable
    return quote(url.encode("iso-8859-1"), safe="%/:=&?~#+!$,;'@()*[]")

def get_or_create(klass, _id=None, **kwargs):
    if _id is None:
        object = klass.objects.filter(**kwargs)
    else:
        object = klass.objects.filter(**{_id : kwargs[_id]})
    if object:
        return object[0]
    else:
        print "add new", klass.__name__, kwargs
        return klass.objects.create(**kwargs)

def read_or_dl(url, name, reset=False):
    print "parsing", url
    if not reset and exists('dump/%s' % name):
        text = open('dump/%s' % name).read()
    else:
        text = urlopen(url).read()
        open('dump/%s' % name, "w").write(text)
    soup = BeautifulSoup(text)
    if soup.title.text == "404 Not Found":
        raise IndexError
    return soup

def table2dic(table):
    dico = {}
    for x, y in zip(table[::2], table[1::2]):
        dico[x.text] = y.text if y.a is None else y.a
    return dico

def clean():
    print "cleaning db"
    map(lambda x: x.objects.all().delete(), (Deputy, Party, CommissionMembership, Document, Question, Analysis, Commission))

@hammer_time
def deputies_list(reset=False):
    soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies", reset)

    for dep in soup('table')[4]('tr'):
        items = dep('td')
        full_name = re.sub('  +', ' ', items[0].a.text)
        url = items[0].a['href']
        party = get_or_create(Party, name=items[1].a.text, url=dict(items[1].a.attrs)['href'])
        email = items[2].a.text
        website = items[3].a['href'] if items[3].a else None
        # yes, one deputies key contains a O instead of an 0, I'm not joking
        lachambre_id = re.search('key=([0-9O]+)', url).groups()[0]
        Deputy.objects.create(full_name=full_name,
                              party=party,
                              url=url,
                              websites=[website] if website else [],
                              lachambre_id=lachambre_id,
                              emails=[email])
        print 'adding new deputy', lachambre_id, full_name, party, email, website if website else ''

def each_deputies():
    for index, deputy in enumerate(Deputy.objects.all()):
        print index, deputy.full_name
        parse_deputy(deputy)

@hammer_time
def parse_deputy(deputy, reset=False):
    soup = read_or_dl(LACHAMBRE_PREFIX + deputy.url, deputy.full_name, reset)
    deputy.language = soup.i.parent.text.split(":")[1]
    deputy.cv = re.sub('  +', ' ', soup('table')[5].p.text)
    if deputy.cv.encode("Utf-8").startswith("Députée"):
        deputy.sex = "F"
    elif deputy.cv.encode("Utf-8").startswith("Député"):
        deputy.sex = "M"
    else:
        deputy.sex = None

    # here we will walk in a list of h4 .. h5 .. div+ .. h5 .. div+
    # look at the bottom of each deputies' page
    membership = soup.find('td', rowspan="1")
    item = membership.h4
    role = None
    while item.nextSibling:
        if hasattr(item, 'tag'):
            if item.name == 'h5':
                role = item.text[6:-1]
            elif item.name == 'div':
                print "linking deputy to commission", item.a.text
                commission = get_or_create(Commission, lachambre_id=int(re.search("com=(\d+)", item.a["href"]).groups()[0]))
                deputy.commissions.append(CommissionMembership.objects.create(commission=commission, name=item.a.text, role=role, url=item.a['href']))
        item = item.nextSibling

    deputy_documents(soup, deputy)
    deputy.save()

@hammer_time
def get_deputy_documents(url, deputy, role, type=None, reset=False):
    print "working on %s %sdocuments" % (role, type + " " if type else '') #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s %s' % (deputy.full_name, type if type else '', role), reset)
    setattr(deputy, "documents_%s%s_url" % (role, type + "_" if type else ''), url)
    setattr(deputy, "documents_%s%s_list" % (role, type + "_" if type else ''), [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add", type if type else '', role, i.tr('td')[1].text
        dico = table2dic(i.table('td'))
        print dico
        getattr(deputy, "documents_%s%s_list" % (role, type + "_" if type else '')).append(get_or_create(Document, _id="lachambre_id",
                                                                                                         lachambre_id=re.search("dossierID=(\d+)", i.a["href"]).groups()[0],
                                                                                                         url=i.a['href'],
                                                                                                         title=dico["Titre :"],
                                                                                                         status_chambre=dico.get("Chambre FR :"),
                                                                                                         status_senat=dico.get("Sénat FR :"),
                                                                                                         date=dico.get("Date :"),
                                                                                                         eurovoc_main_descriptor=dico.get("Desc. Eurovoc principal :"),
                                                                                                         eurovoc_descriptors=map(lambda x: x.strip(), dico.get("Descripteurs Eurovoc :", "").split('|')),
                                                                                                         keywords=map(lambda x: x.strip(), dico.get("Mots-clés libres :", "").split('|'))))

@hammer_time
def get_deputy_questions(url, deputy, type, reset=False):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s' % (deputy.full_name, type), reset)
    setattr(deputy, "questions_%s_url" % type, url)
    setattr(deputy, "questions_%s_list" % type, [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add", type, i.tr('td')[1].text.strip()
        dico = table2dic(i.table('td'))
        print dico
        if type == "written":
            deputy.questions_written_list.append(get_or_create(Question,
                                                               _id="lachambre_id",
                                                               title=dico["Titre"],
                                                               departement=dico[u"Département"],
                                                               lachambre_id=re.search("dossierID=([0-9A-Za-z-]+)", i.a["href"]).groups()[0],
                                                               deposition_date=dico[u"Date de dépôt"],
                                                               eurovoc_descriptors=map(lambda x: x.strip(), dico.get("Descripteurs Eurovoc", "").split('|')),
                                                               keywords=map(lambda x: x.strip(), dico.get(u"Mots-clés libres", "").split("|")),
                                                               url=i.a['href'],
                                                               type=type))
        else:
            getattr(deputy, "questions_%s_list" % type).append(get_or_create(Question,
                                                                             _id="lachambre_id",
                                                                             title=i.table('td')[1].text,
                                                                             reunion_type=i.table('td')[9].text,
                                                                             reunion_date=i.table('td')[7].text,
                                                                             session_id=i.table('td')[5].text,
                                                                             pdf_url=i.table('td')[11].a["href"],
                                                                             lachambre_id=re.search("dossierID=([0-9A-Za-z-]+)", i.a["href"]).groups()[0],
                                                                             eurovoc_descriptors=map(lambda x: x.strip(), i.table('td')[13].text.split('|')) if len(i.table('td')) >= 14 and i.table('td')[12].text == u'Descripteurs Eurovoc :' else [],
                                                                             keywords=map(lambda x: x.strip(), i.table('td')[-1].text.split('|')) if len(i.table('td')) == 16 else [],
                                                                             url=i.a['href'],
                                                                             type=type))

@hammer_time
def get_deputy_analysis(url, deputy, type, reset=False):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s' % (deputy.full_name, type), reset)
    setattr(deputy, "analysis_%s_url" % type, url)
    setattr(deputy, "analysis_%s_list" % type, [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add", type, i.tr('td')[1].text.strip()
        getattr(deputy, "analysis_%s_list" % type).append(get_or_create(Analysis,
                                                                        _id="lachambre_id",
                                                                        lachambre_id=re.search("dossierID=([0-9A-Za-z-]+)", i.a["href"]).groups()[0],
                                                                        url=i.a['href'],
                                                                        type=type))

def deputy_documents(soup, deputy):
    # here we are in the grey black box
    urls = map(lambda x: x['href'], soup('div', **{'class': 'linklist_1'})[1]('a'))

    get_deputy_documents(urls[0], deputy, "author", "principal")
    get_deputy_documents(urls[1], deputy, "signator", "principal")
    get_deputy_documents(urls[2], deputy, "author", "next")
    get_deputy_documents(urls[3], deputy, "signator", "next")
    get_deputy_documents(urls[4], deputy, "rapporter")
    get_deputy_questions(urls[5], deputy, "written")
    # no one seems to do any interpellations nor motions or maybe the website is just broken
    get_deputy_questions(urls[8], deputy, "oral_plenary")
    get_deputy_questions(urls[9], deputy, "oral_commission")
    get_deputy_analysis(urls[10], deputy, "legislatif_work")
    get_deputy_analysis(urls[11], deputy, "parlimentary_control")
    get_deputy_analysis(urls[12], deputy, "divers")

def deputies():
    clean()
    deputies_list()
    each_deputies()

def run():
    deputies()

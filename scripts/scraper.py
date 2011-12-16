# -*- coding:Utf-8 -*-
import re
from os.path import exists
from urllib import urlopen, quote
from BeautifulSoup import BeautifulSoup

from deputies.models import Deputy, Party, CommissionMembership, Document, Question, Analysis

LACHAMBRE_PREFIX="http://www.lachambre.be/kvvcr/"

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
    return BeautifulSoup(text)

def clean():
    print "cleaning db"
    map(lambda x: x.objects.all().delete(), (Deputy, Party, CommissionMembership, Document, Question, Analysis))

def deputies_list():
    soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies")

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
    for deputy in Deputy.objects.all():
        print "parsing", deputy.full_name, deputy.url
        soup = read_or_dl(LACHAMBRE_PREFIX + deputy.url, deputy.full_name)
        deputy.language = soup.i.parent.text.split(":")[1]
        deputy.cv = re.sub('  +', ' ', soup('table')[5].p.text)

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
                    deputy.commissions.append(CommissionMembership.objects.create(name=item.a.text, role=role, url=item.a['href']))
                    print "add commission", role, item.a.text
            item = item.nextSibling

        deputy_documents(soup, deputy)
        deputy.save()

def get_deputy_documents(url, deputy, role, type=None):
    print "working on %s %sdocuments" % (role, type + " " if type else '') #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s %s' % (deputy.full_name, type if type else '', role))
    setattr(deputy, "documents_%s%s_url" % (role, type + "_" if type else ''), url)
    setattr(deputy, "documents_%s%s_list" % (role, type + "_" if type else ''), [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add", type if type else '', role, i.tr('td')[1].text
        getattr(deputy, "documents_%s%s_list" % (role, type + "_" if type else '')).append(Document.objects.create(url=i.a['href'], type=type))

def get_deputy_questions(url, deputy, type):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s' % (deputy.full_name, type))
    setattr(deputy, "questions_%s_url" % type, url)
    setattr(deputy, "questions_%s_list" % type, [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add", type, i.tr('td')[1].text.strip()
        getattr(deputy, "questions_%s_list" % type).append(Question.objects.create(url=i.a['href'], type=type))

def get_deputy_analysis(url, deputy, type):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s' % (deputy.full_name, type))
    setattr(deputy, "analysis_%s_url" % type, url)
    setattr(deputy, "analysis_%s_list" % type, [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add", type, i.tr('td')[1].text.strip()
        getattr(deputy, "analysis_%s_list" % type).append(Analysis.objects.create(url=i.a['href'], type=type))

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

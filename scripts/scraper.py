# -*- coding:Utf-8 -*-
import re
from os.path import exists
from urllib import urlopen, quote
from BeautifulSoup import BeautifulSoup

from deputies.models import Deputy, Party, CommissionMembership, Document

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

def read_or_dl(url, name):
    if exists('dump/%s' % name):
        text = open('dump/%s' % name).read()
    else:
        text = urlopen(url).read()
        open('dump/%s' % name, "w").write(text)
    return BeautifulSoup(text)

def clean():
    map(lambda x: x.objects.all().delete(), (Deputy, Party, CommissionMembership, Document))

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

def deputy_documents(soup, deputy):
    urls = map(lambda x: x['href'], soup('div', **{'class': 'linklist_1'})[1]('a'))

    index = 0
    print "working on main legislatif documents" #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(urls[index]), '%s %s' % (deputy.full_name, "author main documents"))
    deputy.documents_principal_author_url = urls[index]
    deputy.documents_principal_author_list = []
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add main document", i.tr('td')[1].text
        deputy.documents_principal_author_list.append(Document.objects.create(url=i.a['href'], type="principal"))

    index += 1
    print "working on main legislatif documents as signator" #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(urls[index]), '%s %s' % (deputy.full_name, "signator main documents"))
    deputy.documents_principal_signator_url = urls[index]
    deputy.documents_principal_signator_list = []
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add main document", i.tr('td')[1].text
        deputy.documents_principal_signator_list.append(Document.objects.create(url=i.a['href'], type="principal"))

    index += 1
    print "working on next legislatif documents" #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(urls[index]), '%s %s' % (deputy.full_name, "author next documents"))
    deputy.documents_next_author_url = urls[index]
    deputy.documents_next_author_list = []
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add nex document", i.tr('td')[1].text
        deputy.documents_next_author_list.append(Document.objects.create(url=i.a['href'], type="next"))

    index += 1
    print "working on next legislatif documents as signator" #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(urls[index]), '%s %s' % (deputy.full_name, "signator next documents"))
    deputy.documents_next_signator_url = urls[index]
    deputy.documents_next_signator_list = []
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add main document", i.tr('td')[1].text
        deputy.documents_next_signator_list.append(Document.objects.create(url=i.a['href'], type="next"))

    index += 1
    print "working on legislatif documents as rapporter" #, LACHAMBRE_PREFIX + lame_url(urls[index])
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(urls[index]), '%s %s' % (deputy.full_name, "rapporter documents"))
    deputy.documents_next_signator_url = urls[index]
    deputy.documents_next_signator_list = []
    for i in soupsoup('table')[3]('tr', valign="top"):
        print "add main document", i.tr('td')[1].text
        deputy.documents_next_signator_list.append(Document.objects.create(url=i.a['href']))

def deputies():
    clean()
    deputies_list()
    each_deputies()

def run():
    deputies()

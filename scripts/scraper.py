import re
from os.path import exists
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup

from deputies.models import Deputy, Party

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
        open('dump/%s' % name, "w").write(text).close()
    return BeautifulSoup(text)

def clean():
    Deputy.objects.all().delete()
    Party.objects.all().delete()

def deputies():
    soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies")

    for dep in soup.findAll('table')[4].findAll('tr'):
        items = dep.findAll('td')
        full_name = re.sub('  +', ' ', items[0].a.text)
        url = dict(items[0].a.attrs)['href']
        party = get_or_create(Party, name=items[1].a.text, url=dict(items[1].a.attrs)['href'])
        email = items[2].a.text
        website = dict(items[3].a.attrs)['href'] if items[3].a else None
        Deputy.objects.create(full_name=full_name,
                              party=party,
                              url=url,
                              websites=[website] if website else [],
                              emails=[email])
        print 'adding new deputy', full_name, party, email, url, website if website else None

def run():
    deputies()

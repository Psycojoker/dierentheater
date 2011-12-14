import re
from os.path import exists
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
from deputies.models import Deputy

def read_or_dl(url, name):
    if exists('dump/%s' % name):
        text = open('dump/%s' % name).read()
    else:
        text = urlopen(url).read()
        open('dump/%s' % name, "w").write(text).close()
    return BeautifulSoup(text)

def deputies():
    Deputy.objects.all().delete()
    soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies")

    for dep in soup.findAll('table')[4].findAll('tr'):
        items = dep.findAll('td')
        full_name = re.sub('  +', ' ', items[0].a.text)
        party = items[1].a.text
        email = items[2].a.text
        print [full_name], [party], [email]
        Deputy.objects.create(full_name=full_name, emails=[email])

def run():
    deputies()

import re

from deputies.models import Commission, CommissionMembership, Deputy
from utils import read_or_dl, get_or_create, LACHAMBRE_PREFIX
from BeautifulSoup import NavigableString

def commissions():
    soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/comm/commissions&language=fr&cfm=/site/wwwcfm/comm/LstCom.cfm&rightmenu=right_cricra", "commissions list")
    _type = ""
    for i in soup("div", id="story")[1]:
        if not isinstance(i, NavigableString) and (i.h4 or i.a):
            if i.h4:
                _type = i.h4.text
            elif i.a:
                commission = get_or_create(Commission, lachambre_id=int(re.search("com=(\d+)", i.a["href"]).groups()[0]))
                commission.type = _type
                commission.name = i.a.text
                commission.url = i.a["href"]

                commission.save()

    for com in list(Commission.objects.all()):
        handle_commission(com)


def handle_commission(commission):
    soup = read_or_dl(LACHAMBRE_PREFIX + commission.url, "commission %s" % commission.lachambre_id)
    commission.full_name = soup.h1.text
    commission.deputies = []
    seats = {}
    for i in soup('p'):
        role = i.b.text[:-1]
        for dep in i('a'):
            deputy = Deputy.objects.get(lachambre_id=re.search("key=([O0-9]+)", dep["href"]).groups()[0])
            membership = get_or_create(CommissionMembership, deputy=deputy, commission=commission)
            membership.role = role
            membership.save()
            commission.deputies.append(membership.id)
        seats[role] = map(lambda x: (x[0], len(x[1].split(','))), zip(map(lambda x: x.text[:-1], i('b')[1:]), str(i).split("<br />")[1:]))

    commission.seats = seats
    commission.save()

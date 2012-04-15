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

from lachambre.models import Commission, CommissionMembership, Deputy
from utils import read_or_dl_with_nl, get_or_create, LACHAMBRE_PREFIX
from BeautifulSoup import NavigableString

def clean_models():
    logger.debug("cleaning commissions modèles")
    map(lambda x: x.objects.all().delete(), (CommissionMembership, Commission))

def scrape():
    soup, suppe = read_or_dl_with_nl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/comm/commissions&language=fr&cfm=/site/wwwcfm/comm/LstCom.cfm&rightmenu=right_cricra", "commissions list")
    _type = ""
    for i, j in zip(soup("div", id="story")[1], suppe("div", id="story")[1]):
        if not isinstance(i, NavigableString) and (i.h4 or i.a):
            if i.h4:
                _type = i.h4.text
                _type_nl = j.h4.text
            elif i.a:
                commission = get_or_create(Commission, lachambre_id=int(re.search("com=(\d+)", i.a["href"]).groups()[0]))
                commission.type["fr"] = _type
                commission.type["nl"] = _type_nl
                commission.name["fr"] = i.a.text
                commission.name["nl"] = j.a.text
                commission.url = i.a["href"]

                commission.save()

    for com in list(Commission.objects.all()):
        handle_commission(com)


def handle_commission(commission):
    soup, suppe = read_or_dl_with_nl(LACHAMBRE_PREFIX + commission.url, "commission %s" % commission.lachambre_id)
    commission.full_name["fr"] = soup.h1.text
    commission.full_name["nl"] = suppe.h1.text
    commission.deputies = []
    seats = {"fr": {}, "nl": {}}
    for i, j in zip(soup('p'), suppe('p')):
        role = i.b.text[:-1]
        role_nl = j.b.text[:-1]
        for dep in i('a'):
            deputy = Deputy.objects.get(lachambre_id=re.search("key=([O0-9]+)", dep["href"]).groups()[0])
            membership = get_or_create(CommissionMembership, deputy=deputy, commission=commission)
            membership.role = role
            membership.save()
            commission.deputies.append(membership.id)
        seats["fr"][role] = map(lambda x: (x[0], len(x[1].split(','))), zip(map(lambda x: x.text[:-1], i('b')[1:]), str(i).split("<br />")[1:]))
        seats["nl"][role_nl] = map(lambda x: (x[0], len(x[1].split(','))), zip(map(lambda x: x.text[:-1], i('b')[1:]), str(i).split("<br />")[1:]))

    commission.seats = seats
    commission.save()

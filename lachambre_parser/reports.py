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
from lachambre.models import AnnualReport
from utils import read_or_dl_with_nl, get_or_create


def clean_models():
    logger.debug("cleaning annual reports models")
    map(lambda x: x.objects.all().delete(), (AnnualReport,))


def scrape():
    for a, url in enumerate(('http://www.lachambre.be/kvvcr/showpage.cfm?section=none&language=fr&cfm=/site/wwwcfm/rajv/rajvlist.cfm?lastreports=y',
                         'http://www.lachambre.be/kvvcr/showpage.cfm?section=none&language=fr&cfm=/site/wwwcfm/rajv/rajvlist.cfm?lastreports=n')):
        soup, suppe = read_or_dl_with_nl(url, "annual repports %i" % a)

        for i, j in zip(soup.find('div', id="story")('table')[1]('tr', recursive=False)[::5], suppe.find('div', id="story")('table')[1]('tr', recursive=False)[::5]):
            get_or_create(AnnualReport,
                          title={"fr": i('td')[2].text, "nl": j('td')[2].text},
                          date=i('td')[0].text,
                          law_and_article={"fr": i('td')[4].text, "nl": j('td')[4].text},
                          periodicity=re.sub("[^0-9]", "", i('td')[5].text),
                          pdf_url=i('td')[1].a["href"] if i('td')[1].a else "",
                          )

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
from lachambre.models import AnnualReport
from utils import read_or_dl, get_or_create


def annual_reports():
    for a, url in enumerate(('http://www.lachambre.be/kvvcr/showpage.cfm?section=none&language=fr&cfm=/site/wwwcfm/rajv/rajvlist.cfm?lastreports=y',
                         'http://www.lachambre.be/kvvcr/showpage.cfm?section=none&language=fr&cfm=/site/wwwcfm/rajv/rajvlist.cfm?lastreports=n')):
        soup = read_or_dl(url, "annual repports %i" % a)

        for i in soup.find('div', id="story")('table')[1]('tr', recursive=False)[::5]:
            get_or_create(AnnualReport,
                          title=i('td')[2].text,
                          date=i('td')[0].text,
                          law_and_article=i('td')[4].text,
                          periodicity=re.sub("[^0-9]", "", i('td')[5].text),
                          pdf_url=i('td')[1].a["href"] if i('td')[1].a else "",
                         )

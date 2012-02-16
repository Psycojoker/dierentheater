import re
from deputies.models import AnnualReport
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

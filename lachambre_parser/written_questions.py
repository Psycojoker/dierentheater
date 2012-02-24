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

from lachambre.models import WrittenQuestionBulletin, WrittenQuestion
from utils import read_or_dl,\
                  LACHAMBRE_PREFIX,\
                  AccessControlDict,\
                  get_or_create,\
                  get_href_else_blank,\
                  get_items_list_else_empty_list,\
                  dico_get_text,\
                  get_text_else_blank


def written_questions():
    _get_written_question_bulletin()

    for bulletin in list(WrittenQuestionBulletin.objects.filter(url__isnull=False)):
        soup = read_or_dl(LACHAMBRE_PREFIX + bulletin.url, "bulletin %s %s" % (bulletin.lachambre_id, bulletin.legislature))
        if not soup.find('table', 'txt'):
            continue
        for link in soup.find('table', 'txt')('tr', recursive=False):
            if link.a is None:
                continue
            _save_a_written_question(link)


def _get_written_question_bulletin():
    for i in range(48, 54):
        soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/qrva&language=fr&rightmenu=right?legislat=52&cfm=/site/wwwcfm/qrva/qrvaList.cfm?legislat=%i" % i, "bulletin list %i" % i)
        for b in soup('table')[4]('tr')[1:]:
            if i == 53:
                WrittenQuestionBulletin.objects.create(
                    legislature="53",
                    lachambre_id=b('td')[0]('a')[-1].text.split()[-1],
                    date=b('td')[2].text,
                    publication_date=b('td')[3].text,
                    url=b('td')[1].a["href"],
                    pdf_url=b('td')[0].a["href"],
                )
            else:
                WrittenQuestionBulletin.objects.create(
                    legislature=str(i),
                    lachambre_id=b('td')[0]('a')[-1].text.split()[-1],
                    publication_date=b('td')[2].text,
                    url=b('td')[1].a["href"] if b('td')[1].a else None,
                    pdf_url=b('td')[0].a["href"],
                )
            print b('td')[0]('a')[-1].text.split()[-1]


def _save_a_written_question(link):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + link.a["href"], "written question %s" % re.search("dossierID=([0-9A-Z-]+).xml", link.a["href"]).groups()[0])
    data = AccessControlDict(((x.td.text, x('td')[1]) for x in soupsoup.find('table', 'txt')('tr') if x.td.text))
    get_or_create(WrittenQuestion,
                  _id="lachambre_id",
                  lachambre_id=re.search("dossierID=([0-9A-Z-]+).xml", link.a["href"]).groups()[0],
                  title=data["Titre"].text,
                  departement=data[u"Département"].text,
                  sub_departement=data[u"Sous-département"].text,
                  deposition_date=data[u"Date de dépôt"].text,
                  delay_date=dico_get_text(data, u"Date de délai"),
                  publication_date=dico_get_text(data, "Date publication"),
                  # TODO: link to the actual deputy
                  author=data[u"Auteur"].text,
                  language=data[u"Langue"].text,
                  question_status=dico_get_text(data, "Statut question"),
                  status=dico_get_text(data, "Statut"),
                  question=data["Question"],
                  answer=dico_get_text(data, u"Réponse"),
                  publication_reponse_pdf_url=get_href_else_blank(data, u"Publication réponse"),
                  publication_question_pdf_url=get_href_else_blank(data, u"Publication question"),
                  publication_reponse=get_text_else_blank(data, u"Publication réponse"),
                  publication_question=get_text_else_blank(data, u"Publication question"),
                  eurovoc_descriptors=get_items_list_else_empty_list(data, "Descripteurs Eurovoc"),
                  eurovoc_candidats_descriptors=get_items_list_else_empty_list(data, "Candidats-descripteurs Eurovoc"),
                  keywords=get_items_list_else_empty_list(data, u"Mots-clés libres"),
                  url=link.a["href"],
                 )

    data.die_if_got_not_accessed_keys()

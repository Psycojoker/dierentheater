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

from lachambre.models import WrittenQuestionBulletin, WrittenQuestion
from utils import (read_or_dl, read_or_dl_with_nl, LACHAMBRE_PREFIX,
                   AccessControlDict, get_href_else_blank,
                   get_items_list_else_empty_list, dico_get_text,
                   get_text_else_blank, update_or_create)

DOSSIER_ID_REGEX = "dossierID=([0-9A-Za-z-]+).xml"


def clean_models():
    logger.debug("cleaning written questions models")
    map(lambda x: x.objects.all().delete(), (WrittenQuestion, WrittenQuestionBulletin))


def scrape():
    WrittenQuestionBulletin.fetch_list()

    # for bulletin in list(WrittenQuestionBulletin.objects.filter(done=False, url__isnull=False)):
    for bulletin in list(WrittenQuestionBulletin.objects.filter(url__isnull=False)):
        soup = read_or_dl(LACHAMBRE_PREFIX + bulletin.url, "bulletin %s %s" % (bulletin.lachambre_id, bulletin.legislature))
        if not soup.find('table', 'txt'):
            continue
        for link in soup.find('table', 'txt').tbody('tr', recursive=False):
            if link.a is None:
                raise Exception("I should check that")
            _save_a_written_question(link)
        bulletin.done = True
        bulletin.save()


def _save_a_written_question(link):
    soupsoup, suppesuppe = read_or_dl_with_nl(LACHAMBRE_PREFIX + link.a["href"], "written question %s" % re.search(DOSSIER_ID_REGEX, link.a["href"]).groups()[0])
    data = AccessControlDict(((x.td.text.strip(), x('td')[1]) for x in soupsoup.find('table', 'txt')('tr') if x.td.text))
    data_nl = AccessControlDict(((x.td.text.strip(), x('td')[1]) for x in suppesuppe.find('table', 'txt')('tr') if x.td.text))
    print sorted(data.keys())
    print sorted(data_nl.keys())
    update_or_create(WrittenQuestion,
                  _id="lachambre_id",
                  lachambre_id=re.search(DOSSIER_ID_REGEX, link.a["href"]).groups()[0],
                  title={"fr": data["Titre"].text, "nl": data_nl["Titel"].text},
                  departement={"fr": data[u"D\xe9partement"].text, "nl": data_nl[u"Departement"].text},
                  sub_departement={"fr": data[u"Sous-d\xe9partement"].text, "nl": data_nl[u"Sub-departement"].text},
                  deposition_date=data[u"Date de d\xe9p\xf4t"].text,
                  delay_date=dico_get_text(data, u"Date de d\xe9lai"),
                  publication_date=dico_get_text(data, "Date publication"),
                  # TODO: link to the actual deputy
                  author=data[u"Auteur"].text,
                  language=data[u"Langue"].text,
                  question_status={"fr": dico_get_text(data, "Statut question"), "nl": dico_get_text(data_nl, "Status vraag")},
                  status={"fr": dico_get_text(data, "Statut"), "nl": dico_get_text(data_nl, "Status")},
                  question={"fr": u"%s" % data["Question"], "nl": "%s" % data_nl["Vraag"]},
                  answer={"fr": dico_get_text(data, u"R\xe9ponse"), "nl": dico_get_text(data_nl, u"Antwoord")},
                  publication_reponse_pdf_url=get_href_else_blank(data, u"Publication r\xe9ponse"),
                  publication_question_pdf_url=get_href_else_blank(data, u"Publication question"),
                  publication_reponse=get_text_else_blank(data, u"Publication r\xe9ponse"),
                  publication_question=get_text_else_blank(data, u"Publication question"),
                  eurovoc_descriptors={"fr": get_items_list_else_empty_list(data, "Descripteurs Eurovoc"),
                                       "nl": get_items_list_else_empty_list(data_nl, "Eurovoc-descriptoren")},
                  eurovoc_principal_descriptors={"fr": get_items_list_else_empty_list(data, "Desc. Eurovoc principal"),
                                       "nl": get_items_list_else_empty_list(data_nl, "Eurovoc-hoofddescriptor")},
                  eurovoc_candidats_descriptors={"fr": get_items_list_else_empty_list(data, "Candidats-descripteurs Eurovoc"),
                                                 "nl": get_items_list_else_empty_list(data_nl, "Eurovoc kandidaat-descriptoren")},
                  keywords={"fr": get_items_list_else_empty_list(data, u"Mots-cl\xe9s libres"),
                            "nl": get_items_list_else_empty_list(data_nl, u"Vrije trefwoorden")},
                  url=link.a["href"],
                     )

    data.die_if_got_not_accessed_keys()

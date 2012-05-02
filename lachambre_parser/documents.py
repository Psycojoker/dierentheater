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
import sys
import logging
import traceback
logger = logging.getLogger('')

from BeautifulSoup import BeautifulSoup
from lxml import etree

from lachambre.models import Document,\
                            InChargeCommissions,\
                            DocumentPlenary,\
                            DocumentSenatPlenary,\
                            DocumentTimeLine,\
                            Analysis,\
                            Deputy,\
                            OtherDocumentChambrePdf,\
                            DocumentChambre,\
                            DocumentSenat,\
                            DocumentChambrePdf,\
                            DocumentSenatPdf,\
                            OtherDocumentSenatPdf

from utils import read_or_dl,\
                  LACHAMBRE_PREFIX,\
                  get_or_create,\
                  clean_text,\
                  read_or_dl_with_nl,\
                  lxml_read_or_dl_with_nl,\
                  get_text_else_blank

from documents_utils import document_pdf_part_cutter,\
                            document_to_dico

from history.utils import irc


def clean_models():
    logger.debug("cleaning documents models")
    map(lambda x: x.objects.all().delete(), (Document, DocumentTimeLine, DocumentChambre, DocumentChambrePdf, DocumentSenat, DocumentSenatPdf, InChargeCommissions, DocumentPlenary, DocumentSenatPlenary, OtherDocumentSenatPdf, OtherDocumentChambrePdf))


def scrape():
    get_new_documents()
    parse_every_documents()


def parse_every_documents():
    # list otherwise mongodb will timeout if we stay in a query mode
    for document in list(Document.objects.filter(done=False)):
        if document.lachambre_id == 25:
            continue
        try:
            handle_document(document)
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            logger.error("/!\ %s didn't succed! Error: while reparsing document %s" % (document.lachambre_id, e))
            irc("\x034%s didn't succed! Error: while reparsing document %s\x03" % (document.lachambre_id, e))
            irc("Bram: entering ipdb shell")
            e, m, tb = sys.exc_info()
            from ipdb import post_mortem; post_mortem(tb)


def get_new_documents():
    for document_page in read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/flwb&language=fr&rightmenu=right&cfm=ListDocument.cfm", "all documents")('div', **{'class': re.compile("linklist_[01]")}):
        soup, suppe = read_or_dl_with_nl(LACHAMBRE_PREFIX + document_page.a["href"], "document %s" % document_page.a.text)
        for soup, suppe in zip(soup('table')[4]('tr', valign="top"), suppe('table')[4]('tr', valign="top")):
            get_or_create(Document, _id="lachambre_id", title={"fr": soup('div')[1].text, "nl": suppe('div')[1].text}, lachambre_id=soup.div.text, url=soup.a["href"])


def check_for_new_documents():
    for document_page in read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/flwb&language=fr&rightmenu=right&cfm=ListDocument.cfm", "all documents")('div', **{'class': re.compile("linklist_[01]")}):
        soup, suppe = read_or_dl_with_nl(LACHAMBRE_PREFIX + document_page.a["href"], "document %s" % document_page.a.text)
        for soup, suppe in zip(soup('table')[4]('tr', valign="top"), suppe('table')[4]('tr', valign="top")):
            if not Document.objects.filter(lachambre_id=soup.div.text):
                url = soup.a["href"]
                title = soup("div")[1].text
                lachambre_id = soup.div.text
                logger.info("find a new document: %s - [%s] -  %s" % (LACHAMBRE_PREFIX + url, lachambre_id, title))
                document = Document(title={"fr": soup('div')[1].text, "nl": suppe('div')[1].text}, lachambre_id=lachambre_id, url=soup.a["href"])
                handle_document(document)


def parse_a_document(lachambre_id):
    handle_document(Document.objects.get(lachambre_id=lachambre_id))


def handle_document(document):
    soup = read_or_dl(LACHAMBRE_PREFIX + document.url if not document.url.startswith("http") else document.url, "a document %s" % document.lachambre_id)
    document.full_details_url = soup('table')[4].a["href"]
    # fucking stupid hack because BeautifulSoup fails to parse correctly the html
    soup, suppe = lxml_read_or_dl_with_nl(LACHAMBRE_PREFIX + document.url if not document.url.startswith("http") else document.url, "a document %s" % document.lachambre_id)
    table = BeautifulSoup(etree.tostring(soup.xpath('//table')[4], pretty_print=True))
    table_nl = BeautifulSoup(etree.tostring(suppe.xpath('//table')[4], pretty_print=True))
    dico = document_to_dico(list(table.table('tr', recursive=False)))
    dico_nl = document_to_dico(list(table_nl.table('tr', recursive=False)))

    _get_first_level_data(dico, dico_nl, document)
    _get_in_charged_commissions(dico, dico_nl, document)
    _get_plenaries(dico, dico_nl, document)
    _get_senat_plenaries(dico, dico_nl, document)
    _get_competences(dico, dico_nl, document)
    _get_document_chambre(dico, dico_nl, document)
    _get_document_senat(dico, dico_nl, document)

    document.done = True
    document.save_with_history()
    logger.info("parsed document [%s] %s" % (document.lachambre_id, document.title["fr"]))
    dico.die_if_got_not_accessed_keys()


def _get_first_level_data(dico, dico_nl, document):
    document.deposition_date = get_text_else_blank(dico, u"Date de dépôt")
    document.constitution_article["fr"] = clean_text(get_text_else_blank(dico, "Article Constitution"))
    document.constitution_article["nl"] = clean_text(get_text_else_blank(dico_nl, "Artikel Grondwet"))
    if dico.get("Descripteur Eurovoc principal"):
        document.eurovoc_main_descriptor["fr"] = dico["Descripteur Eurovoc principal"]["head"].text
    if dico.get("Eurovoc-hoofddescriptor"):
        document.eurovoc_main_descriptor["nl"] = dico_nl["Eurovoc-hoofddescriptor"]["head"].text
    document.vote_date = get_text_else_blank(dico, "Vote Chambre")
    document.law_date = get_text_else_blank(dico, "Date de la loi")
    document.moniteur_number = get_text_else_blank(dico, u"Moniteur n°")
    document.moniteur_date = get_text_else_blank(dico, u"Date moniteur")
    document.vote_senat_date = get_text_else_blank(dico, u"Vote Sénat")
    document.candidature_vote_date = get_text_else_blank(dico, u"Vote candidature")

    if dico.get("Etat d'avancement"):
        document.status_chambre["fr"] = clean_text(dico["Etat d'avancement"].contents[0])
        document.status_senat["fr"] = clean_text(dico["Etat d'avancement"].contents[2]) if len(dico["Etat d'avancement"]) >= 3 else None
        document.status_chambre["nl"] = clean_text(dico_nl["Stand van zaken"].contents[0])
        document.status_senat["nl"] = clean_text(dico_nl["Stand van zaken"].contents[2]) if len(dico_nl["Stand van zaken"]) >= 3 else None

    if dico.get("Descripteurs Eurovoc"):
        document.eurovoc_descriptors["fr"] = map(lambda x: x.strip(), dico["Descripteurs Eurovoc"]["head"].text.split("|"))
        document.eurovoc_descriptors["nl"] = map(lambda x: x.strip(), dico_nl["Eurovoc descriptoren"]["head"].text.split("|"))
    if dico.get("Candidats-descripteurs Eurovoc"):
        document.eurovoc_candidats_descriptors["fr"] = map(lambda x: x.strip(), dico["Candidats-descripteurs Eurovoc"]["head"].text.split("|"))
        document.eurovoc_candidats_descriptors["nl"] = map(lambda x: x.strip(), dico_nl["Eurovoc kandidaat-descriptoren"]["head"].text.split("|"))
    if dico.get(u"Mots-clés libres"):
        document.keywords["fr"] = map(lambda x: x.strip(), dico[u"Mots-clés libres"]["head"].text.split("|"))
        document.keywords["nl"] = map(lambda x: x.strip(), dico_nl[u"Vrije trefwoorden"]["head"].text.split("|"))
    if dico.get("Documents principaux"):
        document.main_docs["fr"] = map(lambda x: x.strip(), filter(lambda x: x != "<br>", dico["Documents principaux"].contents))
        document.main_docs["nl"] = map(lambda x: x.strip(), filter(lambda x: x != "<br>", dico_nl["Hoodfdocumenten"].contents))


def _get_in_charged_commissions(dico, dico_nl, document):
    document.in_charge_commissions = []
    for key, key_nl in zip(sorted(filter(lambda x: re.match("(\d+. )?COMMISSION CHAMBRE", x), dico.keys())), sorted(filter(lambda x: re.match("(\d+. )?COMMISSIE KAMER", x), dico_nl.keys()))):
        icc = InChargeCommissions()
        icc.visibility["fr"] = clean_text(dico[key]["head"].text).split()[-1]
        icc.visibility["nl"] = clean_text(dico_nl[key_nl]["head"].text).split()[-1]
        icc.commission["fr"] = " ".join(clean_text(dico[key]["head"].text).split()[:-1])
        icc.commission["nl"] = " ".join(clean_text(dico_nl[key_nl]["head"].text).split()[:-1])
        if dico[key].get("Rapporteur"):
            # FIXME link to actual deputies
            icc.rapporters = map(clean_text, dico[key]["Rapporteur"].text.split("\n\t\t\t\t\t"))

        icc.incident = []
        if dico[key].get("Incident"):
            fr = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Incident"].contents[::2])))
            nl = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico_nl[key_nl]["Incident"].contents[::2])))
            for (_date, _type), (_, _type_nl) in zip(fr, nl):
                icc.incident.append({"date": _date, "type": {"fr": _type, "nl": _type_nl}})

        icc.agenda = []
        if dico[key].get("Calendrier"):
            fr = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Calendrier"].contents[::2])))
            nl = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico_nl[key_nl]["Kalender"].contents[::2])))
            for (_date, _type), (_, _type_nl) in zip(fr, nl):
                icc.agenda.append({"date": _date, "type": {"fr": _type, "nl": _type_nl}})

        if dico[key].get("Rapport"):
            icc.rapport = {"url": dico[key]["Rapport"].a["href"], "date": clean_text(dico[key]["Rapport"].contents[-2])}

        icc.save()
        document.in_charge_commissions.append(icc)


def _get_plenaries(dico, dico_nl, document):
    document.plenaries = []
    for key, key_nl in zip(sorted(filter(lambda x: re.match("(\d+. )?SEANCE PLENIERE CHAMBRE", x), dico.keys())),
                           sorted(filter(lambda x: re.match("(\d+. )?PLENAIRE VERGADERING KAMER", x), dico_nl.keys()))):
        pl = DocumentPlenary()
        pl.visibility["fr"] = clean_text(dico[key]["head"].text).split()[-1]
        pl.visibility["nl"] = clean_text(dico_nl[key_nl]["head"].text).split()[-1]
        pl.type["fr"] = " ".join(clean_text(dico[key]["head"].text).split()[:-1])
        pl.type["nl"] = " ".join(clean_text(dico_nl[key_nl]["head"].text).split()[:-1])

        pl.agenda = []
        if dico[key].get("Calendrier"):
            fr = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Calendrier"].contents[::2])))
            nl = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico_nl[key_nl]["Kalender"].contents[::2])))
            for (_date, _type), (_, _type_nl) in zip(fr, nl):
                pl.agenda.append({"date": _date, "type": {"fr": _type, "nl": _type_nl}})

        pl.incident = []
        if dico[key].get("Incident"):
            fr = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Incident"].contents[::2])))
            nl = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico_nl[key_nl]["Incident"].contents[::2])))
            for (_date, _type), (_, _type_nl) in zip(fr, nl):
                pl.incident.append({"date": _date, "type": {"fr": _type, "nl": _type_nl}})

        pl.save()
        document.plenaries.append(pl)


def _get_senat_plenaries(dico, dico_nl, document):
    document.senat_plenaries = []
    for key, key_nl in zip(sorted(filter(lambda x: re.match("(\d+. )?SEANCE PLENIERE SENAT", x), dico.keys())),
                           sorted(filter(lambda x: re.match("(\d+. )?PLENAIRE VERGADERING SENAAT", x), dico_nl.keys()))):
        spl = DocumentSenatPlenary()
        spl.visibility["fr"] = clean_text(dico[key]["head"].text).split()[-1]
        spl.visibility["nl"] = clean_text(dico_nl[key_nl]["head"].text).split()[-1]

        spl.agenda = []
        if dico[key].get("Calendrier"):
            fr = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Calendrier"].contents[::2])))
            nl = filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico_nl[key_nl]["Kalender"].contents[::2])))
            for (_date, _type), (_, _type_nl) in zip(fr, nl):
                spl.agenda.append({"date": _date, "type": {"fr": _type, "nl": _type_nl}})

        spl.save()
        document.senat_plenaries.append(spl)


def _get_competences(dico, dico_nl, document):
    if dico.get(u"Compétence"):
        document.timeline = []
        for (_date, _title), (_, _title_nl) in zip([clean_text(x).split(u" \xa0 ", 1) for x in dico[u"Compétence"]["head"].contents[::2]],
                                                   [clean_text(x).split(u" \xa0 ", 1) for x in dico_nl[u"Bevoegdheid"]["head"].contents[::2]]):
            logger.debug("append time line %s %s %s" % (_date, _title, _title_nl))
            document.timeline.append(DocumentTimeLine.objects.create(title={"fr": _title, "nl": _title_nl}, date=_date))
    if dico.get("Analyse des interventions"):
        document.analysis = get_or_create(Analysis, _id="lachambre_id", lachambre_id=dico["Analyse des interventions"]["head"].a.text, url=dico["Analyse des interventions"]["head"].a["href"])


def _get_document_senat(dico, dico_nl, document):
    if not dico.get(u"Document Sénat"):
        return

    senat_dico = dico[u"Document Sénat"]
    senat_dico_nl = dico_nl[u"Document Senaat"]

    document_senat = DocumentSenat()
    document_senat.deposition_date = senat_dico[u"Date de dépôt"].text
    document_senat.ending_date = get_text_else_blank(senat_dico, u"Date de fin")
    document_senat.type["fr"] = senat_dico[u"Type de document"].text
    document_senat.type["nl"] = senat_dico_nl[u"Document type"].text
    document_senat.comments["fr"] = get_text_else_blank(senat_dico, u'Commentaire').split(' - ')
    document_senat.comments["nl"] = get_text_else_blank(senat_dico_nl, u'Commentaar').split(' - ')
    document_senat.author = clean_text(get_text_else_blank(senat_dico, u"Auteur(s)"))
    document_senat.status["fr"] = get_text_else_blank(senat_dico, u'Statut')
    document_senat.status["nl"] = get_text_else_blank(senat_dico_nl, u'Status')

    url, tipe, session = clean_text(str(senat_dico[u'head']).replace("&#160;", "")).split("<br />")
    _, tipe_nl, _ = clean_text(str(senat_dico_nl[u'head']).replace("&#160;", "")).split("<br />")
    url = re.search('href="([^"]+)', url).groups()[0] if "href" in url else url
    document_senat.pdf = DocumentSenatPdf.objects.create(url=url, type={"fr": tipe.strip(), "nl": tipe_nl.strip()}, session=session.split()[-2])

    if senat_dico.get('Document(s) suivant(s)'):
        for d, d_nl in zip(document_pdf_part_cutter(senat_dico[u'Document(s) suivant(s)']), document_pdf_part_cutter(senat_dico_nl[u'Opvolgend(e) document(en)'])):
            logger.debug("add pdf %s" % clean_text(d[0].font.text))
            doc = OtherDocumentSenatPdf()
            doc.url = d[0].a['href'] if d[0].a else d[0].td.text
            doc.type["fr"] = clean_text(d[0].font.text)
            doc.type["nl"] = clean_text(d_nl[0].font.text)
            doc.date = d[0]('td')[-1].contents[0]
            doc.authors = []
            for dep, dep_nl in zip(d[1:], d_nl[1:]):
                doc.authors.append({"full_name": unicode(dep('td')[-1].contents[2]).strip(), "role": {"fr": dep('td')[-1].i.text[1:-1], "nl": dep_nl('td')[-1].i.text[1:-1]}})
            doc.save()
            document_senat.other_pdfs.append(doc)

    document_senat.save()
    document.document_senat = document_senat


def _get_document_chambre(dico, dico_nl, document):
    if not dico.get("Document Chambre"):
        return

    chambre_dico = dico['Document Chambre']
    chambre_dico_nl = dico_nl['Document Kamer']

    document_chambre = DocumentChambre()
    document_chambre.deposition_date = get_text_else_blank(chambre_dico, u'Date de dépôt')
    document_chambre.type["fr"] = chambre_dico[u'Type de document'].text
    document_chambre.type["nl"] = chambre_dico_nl[u'Document type'].text
    document_chambre.taken_in_account_date = get_text_else_blank(chambre_dico, u'Prise en considération')
    document_chambre.distribution_date = get_text_else_blank(chambre_dico, u'Date de distribution')
    document_chambre.sending_date = get_text_else_blank(chambre_dico, u'Date d\'envoi')
    document_chambre.ending_date = get_text_else_blank(chambre_dico, u'Date de fin')
    document_chambre.status["fr"] = get_text_else_blank(chambre_dico, u'Statut')
    document_chambre.status["nl"] = get_text_else_blank(chambre_dico_nl, u'Status')
    document_chambre.comments["fr"] = get_text_else_blank(chambre_dico, u'Commentaire').split(' ')
    document_chambre.comments["nl"] = get_text_else_blank(chambre_dico_nl, u'Commentaar').split(' ')

    _get_authors(chambre_dico, chambre_dico_nl, document_chambre)

    url, tipe, session = clean_text(str(chambre_dico[u'head']).replace("&#160;", "")).split("<br />")
    _, tipe_nl, _ = clean_text(str(chambre_dico_nl[u'head']).replace("&#160;", "")).split("<br />")
    url = re.search('href="([^"]+)', url).groups()[0] if "href" in url else url
    document_chambre.pdf = DocumentChambrePdf.objects.create(url=url, type={"fr": tipe.strip(), "nl": tipe_nl.strip()}, session=session.split()[-2])

    _get_next_documents(chambre_dico, chambre_dico_nl, document_chambre)

    if chambre_dico.get(u'Document(s) joint(s)/lié(s)'):
        document_chambre.joint_pdfs = [{"url": x.a["href"], "title": {"fr": x.contents[0][1:-1], "nl": y.contents[0][1:-1]}} for x, y in zip(chambre_dico[u'Document(s) joint(s)/lié(s)'],
                                                                                                                                             chambre_dico_nl[u'Gekoppeld(e)/verbonden document(en)'],)]

    document_chambre.save()
    document.document_chambre = document_chambre


def _get_authors(chambre_dico, chambre_dico_nl, document_chambre):
    if chambre_dico.get('Auteur(s)'):
        for (dep, role), (_, role_nl) in zip(zip(chambre_dico[u'Auteur(s)']('a'), chambre_dico[u'Auteur(s)']('i')), zip(chambre_dico[u'Auteur(s)']('a'), chambre_dico[u'Auteur(s)']('i'))):
            lachambre_id = re.search('key=(\d+)', dep['href']).groups()[0]
            deputy = Deputy.objects.get(lachambre_id=lachambre_id)
            document_chambre.authors.append({
                "lachambre_id": deputy.lachambre_id,
                "id": deputy.id,
                "full_name": deputy.full_name,
                "role": {"fr": role.text[1:-1], "nl": role_nl.text[1:-1]}
            })


def _get_next_documents(chambre_dico, chambre_dico_nl, document_chambre):
    if chambre_dico.get('Document(s) suivant(s)'):
        for d, d_nl in zip(document_pdf_part_cutter(chambre_dico[u'Document(s) suivant(s)']), document_pdf_part_cutter(chambre_dico_nl[u'Opvolgend(e) document(en)'])):
            logger.debug("add pdf %s" % clean_text(d[0].font.text))
            doc = OtherDocumentChambrePdf()
            doc.url = d[0].a['href'] if d[0].a else d[0].td.text
            doc.type["fr"] = clean_text(d[0].font.text)
            doc.type["nl"] = clean_text(d_nl[0].font.text)
            doc.distribution_date = d[1]('td')[-1].text
            for dep, dep_nl in zip(d[2:], d_nl[2:]):
                if dep.a:
                    lachambre_id = re.search('key=(\d+)', dep.a["href"]).groups()[0]
                    deputy = Deputy.objects.get(lachambre_id=lachambre_id)
                    doc.authors.append({"lachambre_id": deputy.lachambre_id, "id": deputy.id, "full_name": deputy.full_name, "role": {"fr": dep('td')[-1].i.text[1:-1], "nl": dep_nl('td')[-1].i.text[1:-1]}})
                else:
                    doc.authors.append({"lachambre_id": -1, "id": -1, "full_name": dep('td')[-1].contents[2].strip(), "role": {"fr": dep('td')[-1].i.text[1:-1], "nl": dep_nl('td')[-1].i.text[1:-1]}})
            doc.save()
            document_chambre.other_pdfs.append(doc)

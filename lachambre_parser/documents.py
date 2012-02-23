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

from BeautifulSoup import BeautifulSoup
from lxml import etree

from deputies.models import Document,\
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
                  lxml_read_or_dl,\
                  get_text_else_blank

from documents_utils import document_pdf_part_cutter,\
                            document_to_dico

def documents():
    for document_page in read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/flwb&language=fr&rightmenu=right&cfm=ListDocument.cfm", "all documents")('div', **{'class': re.compile("linklist_[01]")}):
        for soup in read_or_dl(LACHAMBRE_PREFIX + document_page.a["href"], "document %s" % document_page.a.text)('table')[4]('tr', valign="top"):
            get_or_create(Document, _id="lachambre_id", title=soup('div')[1].text, lachambre_id=soup.div.text, url=soup.a["href"])

    for document in list(Document.objects.all()):
        handle_document(document)


def handle_document(document):
    soup = read_or_dl(LACHAMBRE_PREFIX + document.url if not document.url.startswith("http") else document.url, "a document %s" % document.lachambre_id)
    document.full_details_url = soup('table')[4].a["href"]
    document.title = soup.h4.text
    # fucking stupid hack because BeautifulSoup fails to parse correctly the html
    soup = lxml_read_or_dl(LACHAMBRE_PREFIX + document.url if not document.url.startswith("http") else document.url, "a document %s" % document.lachambre_id)
    table = BeautifulSoup(etree.tostring(soup.xpath('//table')[4], pretty_print=True))
    dico = document_to_dico(list(table.table('tr', recursive=False)))

    get_first_level_data(dico, document)
    get_in_charged_commissions(dico, document)
    get_plenaries(dico, document)
    get_senat_plenaries(dico, document)
    get_competences(dico, document)
    get_document_chambre(dico, document)
    get_document_senat(dico, document)

    document.save()
    dico.die_if_got_not_accessed_keys()


def get_first_level_data(dico, document):
    document.deposition_date = dico[u"Date de dépôt"].text
    document.constitution_article = clean_text(get_text_else_blank(dico, "Article Constitution"))
    if dico.get("Descripteur Eurovoc principal"):
        document.eurovoc_main_descriptor = dico["Descripteur Eurovoc principal"]["head"]
    document.vote_date = get_text_else_blank(dico, "Vote Chambre")
    document.law_date = get_text_else_blank(dico, "Date de la loi")
    document.moniteur_number = get_text_else_blank(dico, u"Moniteur n°")
    document.moniteur_date = get_text_else_blank(dico, u"Date moniteur")
    document.vote_senat_date = get_text_else_blank(dico, u"Vote Sénat")
    document.candidature_vote_date = get_text_else_blank(dico, u"Vote candidature")

    if dico.get("Etat d'avancement"):
        document.status_chambre = clean_text(dico["Etat d'avancement"].contents[0])
        document.status_senat = clean_text(dico["Etat d'avancement"].contents[2]) if len(dico["Etat d'avancement"]) >= 3 else None

    if dico.get("Descripteurs Eurovoc"):
        document.eurovoc_descriptors = map(lambda x: x.strip(), dico["Descripteurs Eurovoc"]["head"].text.split("|"))
    if dico.get("Candidats-descripteurs Eurovoc"):
        document.eurovoc_candidats_descriptors = map(lambda x: x.strip(), dico["Candidats-descripteurs Eurovoc"]["head"].text.split("|"))
    if dico.get(u"Mots-clés libres"):
        document.keywords = map(lambda x: x.strip(), dico[u"Mots-clés libres"]["head"].text.split("|"))
    if dico.get("Documents principaux"):
        document.main_docs = map(lambda x: x.strip(), filter(lambda x: x != "<br>", dico["Documents principaux"].contents))


def get_in_charged_commissions(dico, document):
    document.in_charge_commissions = []
    for key in filter(lambda x: re.match("(\d+. )?COMMISSION CHAMBRE", x), dico.keys()):
        icc = InChargeCommissions()
        icc.visibility = clean_text(dico[key]["head"].text).split()[-1]
        icc.commission = " ".join(clean_text(dico[key]["head"].text).split()[:-1])
        if dico[key].get("Rapporteur"):
            # FIXME link to actual deputies
            icc.rapporters = map(clean_text, dico[key]["Rapporteur"].text.split("\n\t\t\t\t\t"))

        icc.incident = []
        if dico[key].get("Incident"):
            for _date, _type in filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Incident"].contents[::2]))):
                icc.incident.append({"date": _date, "type": _type})

        icc.agenda = []
        if dico[key].get("Calendrier"):
            for _date, _type in filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Calendrier"].contents[::2]))):
                icc.agenda.append({"date": _date, "type": _type})

        if dico[key].get("Rapport"):
            icc.rapport = {"url": dico[key]["Rapport"].a["href"], "date": clean_text(dico[key]["Rapport"].contents[-2])}

        icc.save()
        document.in_charge_commissions.append(icc)


def get_plenaries(dico, document):
    document.plenaries = []
    for key in filter(lambda x: re.match("(\d+. )?SEANCE PLENIERE CHAMBRE", x), dico.keys()):
        pl = DocumentPlenary()
        pl.visibility = clean_text(dico[key]["head"].text).split()[-1]
        pl.type = " ".join(clean_text(dico[key]["head"].text).split()[:-1])

        pl.agenda = []
        if dico[key].get("Calendrier"):
            for _date, _type in filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Calendrier"].contents[::2]))):
                pl.agenda.append({"date": _date, "type": _type})

        pl.incident = []
        if dico[key].get("Incident"):
            for _date, _type in filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Incident"].contents[::2]))):
                pl.incident.append({"date": _date, "type": _type})

        pl.save()
        document.plenaries.append(pl)


def get_senat_plenaries(dico, document):
    document.senat_plenaries = []
    for key in filter(lambda x: re.match("(\d+. )?SEANCE PLENIERE SENAT", x), dico.keys()):
        spl = DocumentSenatPlenary()
        spl.visibility = clean_text(dico[key]["head"].text).split()[-1]

        spl.agenda = []
        if dico[key].get("Calendrier"):
            for _date, _type in filter(lambda x: x[0], map(lambda x: x.split(u" \xa0 ", 1), map(clean_text, dico[key]["Calendrier"].contents[::2]))):
                spl.agenda.append({"date": _date, "type": _type})

        spl.save()
        document.senat_plenaries.append(spl)


def get_competences(dico, document):
    if dico.get(u"Compétence"):
        document.timeline = []
        for a, b in [clean_text(x).split(u" \xa0 ", 1) for x in dico[u"Compétence"]["head"].contents[::2]]:
            print "append time line", a, b
            document.timeline.append(DocumentTimeLine.objects.create(title=b, date=a))
    if dico.get("Analyse des interventions"):
        document.analysis = get_or_create(Analysis, _id="lachambre_id", lachambre_id=dico["Analyse des interventions"]["head"].a.text, url=dico["Analyse des interventions"]["head"].a["href"])


def get_document_senat(dico, document):
    if not dico.get(u"Document Sénat"):
        return

    senat_dico = dico[u"Document Sénat"]

    document_senat = DocumentSenat()
    document_senat.deposition_date = senat_dico[u"Date de dépôt"].text
    document_senat.ending_date = get_text_else_blank(senat_dico, u"Date de fin")
    document_senat.type = senat_dico[u"Type de document"].text
    document_senat.comments = get_text_else_blank(senat_dico, u'Commentaire').split(' - ')
    document_senat.author = clean_text(get_text_else_blank(senat_dico, u"Auteur(s)"))
    document_senat.comments = get_text_else_blank(senat_dico, u'Commentaire').split(' - ')
    document_senat.status = get_text_else_blank(senat_dico, u'Statut')

    url, tipe, session = clean_text(str(senat_dico[u'head']).replace("&#160;", "")).split("<br />")
    url = re.search('href="([^"]+)', url).groups()[0] if "href" in url else url
    document_senat.pdf = DocumentSenatPdf.objects.create(url=url, type=tipe.strip(), session=session.split()[-2])

    if senat_dico.get('Document(s) suivant(s)'):
        for d in document_pdf_part_cutter(senat_dico[u'Document(s) suivant(s)']):
            print "add pdf %s" % clean_text(d[0].font.text)
            doc = OtherDocumentSenatPdf()
            doc.url = d[0].a['href'] if d[0].a else d[0].td.text
            doc.type = clean_text(d[0].font.text)
            doc.date = d[0]('td')[-1].contents[0]
            doc.authors = []
            for dep in d[1:]:
                doc.authors.append({"full_name": unicode(dep('td')[-1].contents[2]).strip(), "role": dep('td')[-1].i.text[1:-1]})
            doc.save()
            document_senat.other_pdfs.append(doc)

    document_senat.save()
    document.document_senat = document_senat


def get_document_chambre(dico, document):
    def get_authors(chambre_dico, document_chambre):
        if chambre_dico.get('Auteur(s)'):
            for dep, role in zip(chambre_dico[u'Auteur(s)']('a'), chambre_dico[u'Auteur(s)']('i')):
                lachambre_id = re.search('key=(\d+)', dep['href']).groups()[0]
                deputy = Deputy.objects.get(lachambre_id=lachambre_id)
                document_chambre.authors.append({
                    "lachambre_id": deputy.lachambre_id,
                    "id": deputy.id,
                    "full_name": deputy.full_name,
                    "role": role.text[1:-1]
                })

    def get_next_documents(chambre_dico, document_chambre):
        if chambre_dico.get('Document(s) suivant(s)'):
            for d in document_pdf_part_cutter(chambre_dico[u'Document(s) suivant(s)']):
                print "add pdf %s" % clean_text(d[0].font.text)
                doc = OtherDocumentChambrePdf()
                doc.url = d[0].a['href'] if d[0].a else d[0].td.text
                doc.type = clean_text(d[0].font.text)
                doc.distribution_date = d[1]('td')[-1].text
                for dep in d[2:]:
                    if dep.a:
                        lachambre_id = re.search('key=(\d+)', dep.a["href"]).groups()[0]
                        deputy = Deputy.objects.get(lachambre_id=lachambre_id)
                        doc.authors.append({"lachambre_id": deputy.lachambre_id, "id": deputy.id, "full_name": deputy.full_name, "role": dep('td')[-1].i.text[1:-1]})
                    else:
                        doc.authors.append({"lachambre_id": -1, "id": -1, "full_name": dep('td')[-1].contents[2].strip(), "role": dep('td')[-1].i.text[1:-1]})
                doc.save()
                document_chambre.other_pdfs.append(doc)

    if not dico.get("Document Chambre"):
        return

    chambre_dico = dico['Document Chambre']

    document_chambre = DocumentChambre()
    document_chambre.deposition_date = chambre_dico[u'Date de dépôt'].text
    document_chambre.type = chambre_dico[u'Type de document'].text
    document_chambre.taken_in_account_date = get_text_else_blank(chambre_dico, u'Prise en considération')
    document_chambre.distribution_date = get_text_else_blank(chambre_dico, u'Date de distribution')
    document_chambre.sending_date = get_text_else_blank(chambre_dico, u'Date d\'envoi')
    document_chambre.ending_date = get_text_else_blank(chambre_dico, u'Date de fin')
    document_chambre.status = get_text_else_blank(chambre_dico, u'Statut')
    document_chambre.comments = get_text_else_blank(chambre_dico, u'Commentaire').split(' ')

    get_authors(chambre_dico, document_chambre)

    url, tipe, session = clean_text(str(chambre_dico[u'head']).replace("&#160;", "")).split("<br />")
    url = re.search('href="([^"]+)', url).groups()[0] if "href" in url else url
    document_chambre.pdf = DocumentChambrePdf.objects.create(url=url, type=tipe.strip(), session=session.split()[-2])

    get_next_documents(chambre_dico, document_chambre)

    if chambre_dico.get(u'Document(s) joint(s)/lié(s)'):
        document_chambre.joint_pdfs = [{"url": x.a["href"], "title": x.contents[0][1:-1]} for x in chambre_dico[u'Document(s) joint(s)/lié(s)']]

    document_chambre.save()
    document.document_chambre = document_chambre

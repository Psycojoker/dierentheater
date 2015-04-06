# encoding: utf-8

#  lachambre.be to json sausage machine
#  Copyright (C) 2011  Laurent Peuch <cortex@worlddomination.be>
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
import traceback
import logging
logger = logging.getLogger('')

from BeautifulSoup import BeautifulSoup
from lxml import etree

from json import dumps
from datetime import datetime
from bs4 import NavigableString
from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField, DictField

from scraper import scraper
from scraper.utils import (LACHAMBRE_PREFIX, get_or_create,
                           AccessControlDict, get_href_else_blank,
                           get_items_list_else_empty_list, dico_get_text,
                           get_text_else_blank, update_or_create,
                           DOSSIER_ID_REGEX, clean_text,
                           Parsable)

from .documents_parsing_utils import document_pdf_part_cutter, document_to_dico


class Jsonify(object):
    def json(self):
        data = self.__class__.objects.filter(pk=self.pk).values()[0]
        if "creation_datetime" in data:
            del data["creation_datetime"]
        if "current" in data:
            del data["current"]
        return dumps(data, indent=4)


class Deputy(models.Model, Jsonify, Parsable):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    full_name = models.CharField(max_length=1337)
    first_name = models.CharField(max_length=1337)
    last_name = models.CharField(max_length=1337)
    sex = models.CharField(max_length=1337, null=True)
    emails = ListField()
    party = models.ForeignKey('Party', null=True)
    url = models.CharField(max_length=1337)
    websites = ListField()
    lachambre_id = models.CharField(max_length=1337)
    language = models.CharField(max_length=1337, null=True)
    cv = DictField()
    photo_uri = models.CharField(max_length=1337)

    @classmethod
    def fetch_list(klass, cache=False, sync=False):
        soup = scraper.get("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies")

        for dep in soup.table('tr'):
            items = dep('td')
            url = items[0].a['href']
            lachambre_id = re.search('key=([0-9O]+)', url).groups()[0]

            deputy = Deputy.objects.filter(lachambre_id=lachambre_id)
            full_name = re.sub(" +", " ", items[0].a.text.strip())

            if not deputy:
                logger.info("[NEW] deputy: %s" % full_name)
            deputy = deputy[0] if deputy else Deputy(lachambre_id=lachambre_id)

            if items[1].a.text.strip():
                deputy.party = get_or_create(Party, name=items[1].a.text.strip(), url=dict(items[1].a.attrs)['href'])

            email = items[2].a.text
            website = items[3].a['href'] if items[3].a else None

            if email not in deputy.emails:
                deputy.emails.append(email)
            if website not in deputy.websites:
                deputy.websites.append(website)

            deputy.full_name = full_name
            deputy.url = url
            deputy.save()

        for index, deputy in enumerate(list(Deputy.objects.all())):
            logger.debug("%s %s" % (index, deputy.full_name))
            klass.fetch_one(deputy, cache=cache, sync=sync)

    @classmethod
    def fetch_one(klass, deputy, cache=False, sync=False):
        soup, suppe = scraper.get_with_nl(LACHAMBRE_PREFIX + deputy.url, deputy.full_name)

        deputy.photo_uri = "http://www.lachambre.be" + soup.table.img["src"]
        # XXX can't get this anymore I guess :(
        # deputy.language = soup.table.i.parent.text.split(":")[1] if soup.i else None
        deputy.cv["fr"] = re.sub('  +', ' ', soup('table')[1].p.text).strip()
        deputy.cv["nl"] = re.sub('  +', ' ', suppe('table')[1].p.text).strip()
        if deputy.cv["fr"].encode("Utf-8").startswith("Députée"):
            deputy.sex = "F"
        elif deputy.cv["fr"].encode("Utf-8").startswith("Député"):
            deputy.sex = "M"
        else:
            deputy.sex = None

        Deputy.split_deputy_full_name(deputy, soup)
        deputy.save()

    @staticmethod
    def split_deputy_full_name(deputy, soup):
        return
        # stupid special case
        from ipdb import set_trace
        set_trace()
        if deputy.full_name == "Fernandez Fernandez Julie":
            deputy.first_name = "Julie"
            deputy.last_name = "Fernandez Fernandez"
        elif deputy.full_name == "Dedecker Jean Marie":
            deputy.first_name = "Jean Marie"
            deputy.last_name = "Dedecker"
        # here we guess the first and last name, for that we compare
        # deputy.full_name that is in the form of "de Donnea
        # François-Xavier" and the name of the deputy page which is in the
        # form of "François-Xavier de Donnea"
        elif len(deputy.full_name.split(" ")) > 2:
            it = 0
            while it < len(deputy.full_name.split(" ")):
                if soup.h2.text.split(" ")[it] != deputy.full_name.split(" ")[-(it + 1)]:
                    break
                it += 1
                logger.debug("%s %s %s" % (it, soup.h2.text.split(" ")[it], deputy.full_name.split(" ")[-(it + 1)]))
            if not it:
                raise Exception
            deputy.first_name = " ".join(soup.h2.text.split(" ")[:it]).strip()
            deputy.last_name = " ".join(soup.h2.text.split(" ")[it:]).strip()
            logger.debug("%s %s" % ([deputy.first_name], [deputy.last_name]))
        else:
            # if there is only 2 words just split this in 2
            deputy.first_name = deputy.full_name.split(" ")[1].strip()
            deputy.last_name = deputy.full_name.split(" ")[0].strip()
            logger.debug("%s %s" % ([deputy.first_name], [deputy.last_name]))



    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

    class Meta:
        ordering = ["full_name"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url


class Party(models.Model, Jsonify):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    name = models.CharField(max_length=1337)
    url = models.URLField()


    def __unicode__(self):
        return self.name

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url

    class Meta:
        ordering = ["name"]


class Commission(models.Model, Jsonify, Parsable):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    lachambre_id = models.IntegerField()
    name = DictField()
    full_name = DictField()
    url = models.URLField()
    type = DictField()
    deputies = ListField(models.ForeignKey("CommissionMembership"))
    seats = DictField()

    @classmethod
    def fetch_list(klass, cache=False, sync=False):
        soup, suppe = scraper.get_with_nl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/comm/commissions&language=fr&cfm=/site/wwwcfm/comm/LstCom.cfm&rightmenu=right_cricra", "commissions list")
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
            klass.fetch_one(com, cache=cache, sync=sync)

    @classmethod
    def fetch_one(klass, commission, cache=False, sync=False):
        soup, suppe = scraper.get_with_nl(LACHAMBRE_PREFIX + commission.url, "commission %s" % commission.lachambre_id)
        commission.full_name["fr"] = soup.h1.text
        commission.full_name["nl"] = suppe.h1.text
        commission.deputies = []
        seats = {"fr": {}, "nl": {}}
        for i, j in zip(soup('p')[2:], suppe('p')[2:]):
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

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]


class CommissionMembership(models.Model, Jsonify):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    role = models.CharField(max_length=1337)
    role_en = models.CharField(max_length=1337)
    commission = models.ForeignKey("Commission")
    deputy = models.ForeignKey("Deputy")



class Document(models.Model, Jsonify, Parsable):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    title = DictField()
    url = models.CharField(max_length=1337)
    full_details_url = models.CharField(max_length=1337)
    status_chambre = DictField()
    status_senat = DictField()
    deposition_date = models.CharField(max_length=1337, null=True)
    constitution_article = DictField()
    in_charge_commissions = ListField(EmbeddedModelField('InChargeCommissions'))
    plenaries = ListField(EmbeddedModelField('DocumentPlenary'))
    senat_plenaries = ListField(EmbeddedModelField('DocumentSenatPlenary'))
    timeline = ListField(EmbeddedModelField('DocumentTimeLine'))
    eurovoc_main_descriptor = DictField()
    eurovoc_descriptors = DictField()
    eurovoc_candidats_descriptors = DictField()
    keywords = DictField()
    lachambre_id = models.IntegerField()
    analysis = EmbeddedModelField('Analysis', null=True)
    document_chambre = EmbeddedModelField('DocumentChambre', null=True)
    document_senat = EmbeddedModelField('DocumentSenat', null=True)
    vote_date = models.CharField(max_length=1337)
    vote_senat_date = models.CharField(max_length=1337)
    law_date = models.CharField(max_length=1337)
    moniteur_number = models.CharField(max_length=1337)
    moniteur_date = models.CharField(max_length=1337)
    main_docs = DictField()
    candidature_vote_date = models.CharField(max_length=1337)
    done = models.BooleanField(default=False)

    @classmethod
    def fetch_list(klass, cache=False, sync=False):
        for document_page in scraper.get("http://www.lachambre.be/kvvcr/showpage.cfm?section=/flwb&language=fr&rightmenu=right&cfm=ListDocument.cfm", "all documents")('div', **{'class': re.compile("linklist_[01]")}):
            soup, suppe = scraper.get_with_nl(LACHAMBRE_PREFIX + document_page.a["href"], "document %s" % document_page.a.text)
            for soup, suppe in zip(soup.table('tr'), suppe.table('tr')):
                get_or_create(Document, _id="lachambre_id", title={"fr": soup('div')[1].text, "nl": suppe('div')[1].text}, lachambre_id=soup.div.text, url=soup.a["href"])

        # list otherwise mongodb will timeout if we stay in a query mode
        for document in list(Document.objects.filter(done=False)):
            if document.lachambre_id == 25:
                continue
            try:
                klass.fetch_one(document)
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                logger.error("/!\ %s didn't succed! Error: while reparsing document %s" % (document.lachambre_id, e))


    @staticmethod
    def fetch_one(klass, document, cache=False, sync=False):
        soup = scraper.get(LACHAMBRE_PREFIX + document.url if not document.url.startswith("http") else document.url, "a document %s" % document.lachambre_id)
        document.full_details_url = soup.table.a["href"]
        # fucking stupid hack because BeautifulSoup fails to parse correctly the html
        soup, suppe = scraper.lxml_get_with_nl(LACHAMBRE_PREFIX + document.url if not document.url.startswith("http") else document.url, "a document %s" % document.lachambre_id)
        table = BeautifulSoup(etree.tostring(soup.xpath('//table')[0], pretty_print=True))
        table_nl = BeautifulSoup(etree.tostring(suppe.xpath('//table')[0], pretty_print=True))
        dico = document_to_dico(list(table.table('tr', recursive=False)))
        dico_nl = document_to_dico(list(table_nl.table('tr', recursive=False)))

        del dico[""]
        del dico_nl[""]

        klass._get_first_level_data(dico, dico_nl, document)
        klass._get_in_charged_commissions(dico, dico_nl, document)
        klass._get_plenaries(dico, dico_nl, document)
        klass._get_senat_plenaries(dico, dico_nl, document)
        klass._get_competences(dico, dico_nl, document)
        klass._get_document_chambre(dico, dico_nl, document)
        klass._get_document_senat(dico, dico_nl, document)

        document.done = True
        document.save()
        logger.info("parsed document [%s] %s" % (document.lachambre_id, document.title["fr"]))
        dico.die_if_got_not_accessed_keys()


    @staticmethod
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
        if dico.get("Stand van zaken"):
            document.status_chambre["nl"] = clean_text(dico_nl["Stand van zaken"].contents[0])
            document.status_senat["nl"] = clean_text(dico_nl["Stand van zaken"].contents[2]) if len(dico_nl["Stand van zaken"]) >= 3 else None

        if dico.get("Descripteurs Eurovoc"):
            document.eurovoc_descriptors["fr"] = map(lambda x: x.strip(), dico["Descripteurs Eurovoc"]["head"].text.split("|"))
        if dico.get("Eurovoc descriptoren"):
            document.eurovoc_descriptors["nl"] = map(lambda x: x.strip(), dico_nl["Eurovoc descriptoren"]["head"].text.split("|"))
        if dico.get("Candidats-descripteurs Eurovoc"):
            document.eurovoc_candidats_descriptors["fr"] = map(lambda x: x.strip(), dico["Candidats-descripteurs Eurovoc"]["head"].text.split("|"))
        if dico.get("Eurovoc kandidaat-descriptoren"):
            document.eurovoc_candidats_descriptors["nl"] = map(lambda x: x.strip(), dico_nl["Eurovoc kandidaat-descriptoren"]["head"].text.split("|"))
        if dico.get(u"Mots-clés libres"):
            document.keywords["fr"] = map(lambda x: x.strip(), dico[u"Mots-clés libres"]["head"].text.split("|"))
        if dico.get(u"Vrije trefwoorden"):
            document.keywords["nl"] = map(lambda x: x.strip(), dico_nl[u"Vrije trefwoorden"]["head"].text.split("|"))
        if dico.get("Documents principaux"):
            document.main_docs["fr"] = map(lambda x: x.strip(), filter(lambda x: x != "<br>", dico["Documents principaux"].contents))
        if dico.get("Hoodfdocumenten"):
            document.main_docs["nl"] = map(lambda x: x.strip(), filter(lambda x: x != "<br>", dico_nl["Hoodfdocumenten"].contents))


    @staticmethod
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


    @staticmethod
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


    @staticmethod
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


    @staticmethod
    def _get_competences(dico, dico_nl, document):
        # FIXME: meh, DRY
        if dico.get(u"Compétence") and dico_nl.get(u"Bevoegdheid"):
            document.timeline = []
            for (_date, _title), (_, _title_nl) in zip([clean_text(x).split(u" \xa0 ", 1) for x in dico[u"Compétence"]["head"].contents[::2]],
                                                       [clean_text(x).split(u" \xa0 ", 1) for x in dico_nl[u"Bevoegdheid"]["head"].contents[::2]]):
                logger.debug("append time line %s %s %s" % (_date, _title, _title_nl))
                document.timeline.append(DocumentTimeLine.objects.create(title={"fr": _title, "nl": _title_nl}, date=_date))
        elif dico.get(u"Compétence"):
            document.timeline = []
            for (_date, _title) in [clean_text(x).split(u" \xa0 ", 1) for x in dico[u"Compétence"]["head"].contents[::2]]:
                logger.debug("append time line %s %s %s" % (_date, _title, ""))
                document.timeline.append(DocumentTimeLine.objects.create(title={"fr": _title, "nl": ""}, date=_date))
        elif dico_nl.get(u"Bevoegdheid"):
            document.timeline = []
            for (_date, _title_nl) in [clean_text(x).split(u" \xa0 ", 1) for x in dico_nl[u"Bevoegdheid"]["head"].contents[::2]]:
                logger.debug("append time line %s %s %s" % (_date, "", _title_nl))
                document.timeline.append(DocumentTimeLine.objects.create(title={"fr": "", "nl": _title_nl}, date=_date))
        if dico.get("Analyse des interventions"):
            document.analysis = get_or_create(Analysis, _id="lachambre_id", lachambre_id=dico["Analyse des interventions"]["head"].a.text, url=dico["Analyse des interventions"]["head"].a["href"])


    @staticmethod
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


    @staticmethod
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

        Document._get_authors(chambre_dico, chambre_dico_nl, document_chambre)

        url, tipe, session = clean_text(str(chambre_dico[u'head']).replace("&#160;", "")).split("<br />")
        _, tipe_nl, _ = clean_text(str(chambre_dico_nl[u'head']).replace("&#160;", "")).split("<br />")
        url = re.search('href="([^"]+)', url).groups()[0] if "href" in url else url
        document_chambre.pdf = DocumentChambrePdf.objects.create(url=url, type={"fr": tipe.strip(), "nl": tipe_nl.strip()}, session=session.split()[-2])

        Document._get_next_documents(chambre_dico, chambre_dico_nl, document_chambre)

        if chambre_dico.get(u'Document(s) joint(s)/lié(s)'):
            document_chambre.joint_pdfs = [{"url": x.a["href"], "title": {"fr": x.contents[0][1:-1], "nl": y.contents[0][1:-1]}} for x, y in zip(chambre_dico[u'Document(s) joint(s)/lié(s)'],
                                                                                                                                                 chambre_dico_nl[u'Gekoppeld(e)/verbonden document(en)'],)]

        document_chambre.save()
        document.document_chambre = document_chambre


    @staticmethod
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


    @staticmethod
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

    def __unicode__(self):
        return "%s - %s" % (self.lachambre_id, self.title["fr"])

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url

    class Meta:
        ordering = ["-lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", -1)]
        ]


class InChargeCommissions(models.Model):
    visibility = DictField()
    # need to turn that into a EmbeddedModelField(commissions) in the futur
    # when the commissions will be parsed
    commission = DictField()
    rapporters = ListField()
    agenda = ListField()
    incident = ListField()
    rapport = DictField()


class DocumentPlenary(models.Model):
    visibility = DictField()
    type = DictField()
    agenda = ListField()
    incident = ListField()


class DocumentSenatPlenary(models.Model):
    visibility = DictField()
    agenda = ListField()


class DocumentChambre(models.Model):
    deposition_date = models.CharField(max_length=1337)
    type = DictField()
    taken_in_account_date = models.CharField(max_length=1337)
    distribution_date = models.CharField(max_length=1337)
    sending_date = models.CharField(max_length=1337)
    ending_date = models.CharField(max_length=1337)
    status = DictField()
    authors = ListField()
    comments = DictField()
    pdf = EmbeddedModelField('DocumentChambrePdf')
    other_pdfs = ListField(EmbeddedModelField('OtherDocumentChambrePdf'))
    joint_pdfs = ListField()


class DocumentChambrePdf(models.Model):
    url = models.CharField(max_length=1337)
    session = models.CharField(max_length=1337)
    type = DictField()


class DocumentSenat(models.Model):
    deposition_date = models.CharField(max_length=1337)
    type = DictField()
    comments = DictField()
    ending_date = models.CharField(max_length=1337)
    author = models.CharField(max_length=1337)
    pdf = EmbeddedModelField('DocumentSenatPdf')
    comments = DictField()
    status = DictField()
    other_pdfs = ListField(EmbeddedModelField('OtherDocumentSenatPdf'))


class DocumentSenatPdf(models.Model):
    url = models.CharField(max_length=1337)
    session = models.CharField(max_length=1337)
    type = DictField()


class OtherDocumentSenatPdf(models.Model):
    url = models.CharField(max_length=1337)
    type = DictField()
    date = models.CharField(max_length=1337)
    authors = ListField()


class OtherDocumentChambrePdf(models.Model):
    url = models.CharField(max_length=1337)
    type = DictField()
    distribution_date = models.CharField(max_length=1337)
    authors = ListField()


class DocumentTimeLine(models.Model):
    title = DictField()
    date = models.CharField(max_length=1337)


class WrittenQuestion(models.Model, Jsonify, Parsable):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    title = DictField()
    departement = DictField()
    sub_departement = DictField()
    author = models.CharField(max_length=1337)
    deposition_date = models.CharField(max_length=1337)
    delay_date = models.CharField(max_length=1337, null=True)
    eurovoc_descriptors = DictField()
    eurovoc_principal_descriptors = DictField()
    eurovoc_candidats_descriptors = DictField()
    keywords = DictField()
    url = models.URLField()
    lachambre_id = models.CharField(max_length=1337)
    language = models.CharField(max_length=1337)
    status = DictField()
    question_status = DictField()
    publication_date = models.CharField(max_length=1337)
    question = DictField()
    answer = DictField()
    publication_reponse_pdf_url = models.CharField(max_length=1337)
    publication_question_pdf_url = models.CharField(max_length=1337)
    publication_reponse = models.CharField(max_length=1337, null=True)
    publication_question = models.CharField(max_length=1337, null=True)

    @classmethod
    def fetch_list(klass, cache=False, sync=False):
        WrittenQuestionBulletin.fetch_list()

        for bulletin in list(WrittenQuestionBulletin.objects.filter(url__isnull=False)):
            soup = scraper.get(LACHAMBRE_PREFIX + bulletin.url, "bulletin %s %s" % (bulletin.lachambre_id, bulletin.legislature))
            if not soup.find('table', 'txt'):
                continue
            for link in soup.find('table', 'txt').tbody('tr', recursive=False):
                if link.a is None:
                    raise Exception("I should check that")
                klass.fetch_one(link)
            bulletin.done = True
            bulletin.save()

    @classmethod
    def fetch_one(klass, link, cache=False, sync=False):
        soupsoup, suppesuppe = scraper.get_with_nl(LACHAMBRE_PREFIX + link.a["href"], "written question %s" % re.search(DOSSIER_ID_REGEX, link.a["href"]).groups()[0])
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

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]


class WrittenQuestionBulletin(models.Model, Jsonify, Parsable):
    lachambre_id = models.CharField(max_length=1337)
    date = models.CharField(max_length=1337, null=True)
    publication_date = models.CharField(max_length=1337)
    url = models.URLField(null=True)
    pdf_url = models.URLField()
    legislature = models.CharField(max_length=1337)
    done = models.BooleanField(default=False)

    @classmethod
    def fetch_list(klass, cache=False, sync=False):
        for i in range(48, 55):
            soup = scraper.get("http://www.lachambre.be/kvvcr/showpage.cfm?section=/qrva&language=fr&rightmenu=right?legislat=52&cfm=/site/wwwcfm/qrva/qrvaList.cfm?legislat=%i" % i, "bulletin list %i" % i)
            for b in soup.table('tr')[1:]:
                try:
                    klass.fetch_one(soup, legislation=i)
                except TypeError, e:
                    logger.debug("Error on written question bulleting of legislation %s:" % i, e)
                    continue

    @classmethod
    def fetch_one(klass, soup, legislation, cache=False, sync=False):
        if legislation == 54:
            get_or_create(WrittenQuestionBulletin,
                          legislature="53",
                          lachambre_id=soup('td')[0]('a')[-1].text.split()[-1],
                          date=soup('td')[2].text,
                          publication_date=soup('td')[3].text,
                          url=soup('td')[1].a["href"],
                          pdf_url=soup('td')[0].a["href"],
                          )
        else:
            get_or_create(WrittenQuestionBulletin,
                          legislature=str(legislation),
                          lachambre_id=soup('td')[0]('a')[-1].text.split()[-1],
                          publication_date=soup('td')[2].text,
                          url=soup('td')[1].a["href"] if soup('td')[1].a else None,
                          pdf_url=soup('td')[0].a["href"],
                          )
            logger.debug("%s" % soup('td')[0]('a')[-1].text.split()[-1])

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url


class Question(models.Model, Jsonify):
    title = models.CharField(max_length=1337)
    reunion_type = models.CharField(max_length=1337, null=True)
    reunion_date = models.CharField(max_length=1337, null=True)
    session_id = models.CharField(max_length=1337)
    eurovoc_descriptors = ListField()
    keywords = ListField()
    pdf_url = models.URLField(null=True)
    url = models.URLField()
    type = models.CharField(max_length=1337)
    lachambre_id = models.CharField(max_length=1337)

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url


class Analysis(models.Model, Jsonify):
    title = models.CharField(max_length=1337)
    descriptor = models.CharField(max_length=1337)
    url = models.URLField()
    type = models.CharField(max_length=1337)
    lachambre_id = models.CharField(max_length=1337)

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url


class AnnualReport(models.Model, Jsonify, Parsable):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    title = DictField()
    date = models.CharField(max_length=1337)
    law_and_article = DictField()
    periodicity = models.CharField(max_length=1337)
    pdf_url = models.URLField()

    @classmethod
    def fetch_list(klass, cache=False, sync=False):
        for a, url in enumerate(('http://www.lachambre.be/kvvcr/showpage.cfm?section=none&language=fr&cfm=/site/wwwcfm/rajv/rajvlist.cfm?lastreports=y',
                             'http://www.lachambre.be/kvvcr/showpage.cfm?section=none&language=fr&cfm=/site/wwwcfm/rajv/rajvlist.cfm?lastreports=n')):
            soup, suppe = scraper.get_with_nl(url, "annual repports %i" % a)

            for i, j in zip(soup.find('div', id="story")('table')[1].tbody('tr', recursive=False)[::5], suppe.find('div', id="story")('table')[1].tbody('tr', recursive=False)[::5]):
                get_or_create(AnnualReport,
                              title={"fr": i('td')[2].text, "nl": j('td')[2].text},
                              date=i('td')[0].text,
                              law_and_article={"fr": i('td')[4].text, "nl": j('td')[4].text},
                              periodicity=re.sub("[^0-9]", "", i('td')[5].text),
                              pdf_url=i('td')[1].a["href"] if i('td')[1].a else "",
                              )

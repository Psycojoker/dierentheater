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
import logging
logger = logging.getLogger('')

from json import dumps
from datetime import datetime
from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField, DictField

from lachambre_parser.utils import (read_or_dl, read_or_dl_with_nl, LACHAMBRE_PREFIX,
                                    get_or_create, AccessControlDict, get_href_else_blank,
                                    get_items_list_else_empty_list, dico_get_text,
                                    get_text_else_blank, update_or_create, DOSSIER_ID_REGEX)

from .utils import Parsable


class Jsonify(object):
    def json(self):
        data = self.__class__.objects.filter(pk=self.pk).values()[0]
        if "creation_datetime" in data:
            del data["creation_datetime"]
        if "current" in data:
            del data["current"]
        return dumps(data, indent=4)


class Deputy(models.Model, Jsonify):
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
    def fetch_list(klass):
        soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies")

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
            klass.fetch_one(deputy)

    @classmethod
    def fetch_one(klass, deputy):
        soup, suppe = read_or_dl_with_nl(LACHAMBRE_PREFIX + deputy.url, deputy.full_name)

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


class CommissionMembership(models.Model, Jsonify):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    role = models.CharField(max_length=1337)
    role_en = models.CharField(max_length=1337)
    commission = models.ForeignKey("Commission")
    deputy = models.ForeignKey("Deputy")



class Commission(models.Model, Jsonify):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    lachambre_id = models.IntegerField()
    name = DictField()
    full_name = DictField()
    url = models.URLField()
    type = DictField()
    deputies = ListField(models.ForeignKey(CommissionMembership))
    seats = DictField()


    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]


class Document(models.Model, Jsonify):
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
    def fetch_list(klass):
        WrittenQuestionBulletin.fetch_list()

        for bulletin in list(WrittenQuestionBulletin.objects.filter(url__isnull=False)):
            soup = read_or_dl(LACHAMBRE_PREFIX + bulletin.url, "bulletin %s %s" % (bulletin.lachambre_id, bulletin.legislature))
            if not soup.find('table', 'txt'):
                continue
            for link in soup.find('table', 'txt').tbody('tr', recursive=False):
                if link.a is None:
                    raise Exception("I should check that")
                klass.fetch_one(link)
            bulletin.done = True
            bulletin.save()

    @classmethod
    def fetch_one(klass, link):
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
    def fetch_list(klass):
        for i in range(48, 55):
            soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/qrva&language=fr&rightmenu=right?legislat=52&cfm=/site/wwwcfm/qrva/qrvaList.cfm?legislat=%i" % i, "bulletin list %i" % i)
            for b in soup.table('tr')[1:]:
                try:
                    klass.fetch_one(soup, legislation=i)
                except TypeError, e:
                    logger.debug("Error on written question bulleting of legislation %s:" % i, e)
                    continue

    @classmethod
    def fetch_one(klass, soup, legislation):
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


class AnnualReport(models.Model, Jsonify):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    title = DictField()
    date = models.CharField(max_length=1337)
    law_and_article = DictField()
    periodicity = models.CharField(max_length=1337)
    pdf_url = models.URLField()

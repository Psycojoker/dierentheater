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

import logging
logger = logging.getLogger('')

from json import dumps
from datetime import datetime
from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField, DictField


LACHAMBRE_PREFIX = "http://www.lachambre.be/kvvcr/"


def diff(row, other):
    if row.__class__ != other.__class__:
        return True

    for field in map(lambda x: x.attname, row._meta.fields):
        if not isinstance(field, (EmbeddedModelField)):
            if getattr(row, field) != getattr(other, field):
                logger.info("[%s] '%s' != '%s'" % (field, getattr(row, field), getattr(other, field)))
                return True

    return False


class Jsonify(object):
    def json(self):
        return dumps(self.__class__.objects.filter(pk=self.pk).values()[0], indent=4)


def history(klass):
    def save(self, *args, **kwargs):
        in_db = self.__class__.objects.filter(id=self.id)
        if not in_db:
            return models.Model.save(self, *args, **kwargs)
        assert len(in_db) == 1
        in_db = in_db[0]
        if diff(self, in_db):
            # duplicated the in_db data into another model that contains the old data
            logger.info("[%s]'%s' has been modified" % (self.lachambre_id if hasattr(self, "lachambre_id") else self.id, self))
            self.__class__.objects.create(current=False,
                                          **dict((x.attname, getattr(in_db, x.attname))
                                                    for x in in_db._meta.fields
                                                        if not isinstance(x, models.AutoField)
                                                           and x.attname != "current"))

        return models.Model.save(self, *args, **kwargs)

    klass.save_with_history = save
    return klass


class Deputy(models.Model, Jsonify):
    current = models.BooleanField(default=True)
    creation_datetime = models.DateTimeField(default=datetime.now)
    full_name = models.CharField(max_length=1337, unique=True)
    first_name = models.CharField(max_length=1337)
    last_name = models.CharField(max_length=1337)
    sex = models.CharField(max_length=1337, null=True)
    emails = ListField()
    party = models.ForeignKey('Party')
    url = models.CharField(max_length=1337)
    websites = ListField()
    lachambre_id = models.CharField(max_length=1337, unique=True)
    language = models.CharField(max_length=1337, null=True)
    cv = DictField()
    #commissions = ListField(EmbeddedModelField('CommissionMembership'))

    #documents_principal_author_url = models.URLField()
    #documents_principal_author_list = ListField(EmbeddedModelField('Document'))
    #documents_principal_signator_url = models.URLField()
    #documents_principal_signator_list = ListField(EmbeddedModelField('Document'))

    #documents_next_author_url = models.URLField()
    #documents_next_author_list = ListField(EmbeddedModelField('Document'))
    #documents_next_signator_url = models.URLField()
    #documents_next_signator_list = ListField(EmbeddedModelField('Document'))

    #documents_rapporter_url = models.URLField()
    #documents_rapporter_list = ListField(EmbeddedModelField('Document'))

    #questions_written_url = models.URLField()
    #questions_written_list = ListField(EmbeddedModelField('WrittenQuestion'))

    #questions_oral_plenary_url = models.URLField()
    #questions_oral_plenary_list = ListField(EmbeddedModelField('Question'))

    #questions_oral_commission_url = models.URLField()
    #questions_oral_commission_list = ListField(EmbeddedModelField('Question'))

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]


class Party(models.Model, Jsonify):
    name = models.CharField(max_length=1337)
    url = models.URLField()

    def __unicode__(self):
        return self.name


class CommissionMembership(models.Model, Jsonify):
    role = models.CharField(max_length=1337)
    role_en = models.CharField(max_length=1337)
    commission = models.ForeignKey("Commission")
    deputy = models.ForeignKey("Deputy")


class Commission(models.Model, Jsonify):
    lachambre_id = models.IntegerField(unique=True)
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
    lachambre_id = models.IntegerField(unique=True)
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
        return "%s - %s" % (self.lachambre_id, self.title)

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


class WrittenQuestion(models.Model, Jsonify):
    title = DictField()
    departement = DictField()
    sub_departement = DictField()
    author = models.CharField(max_length=1337)
    deposition_date = models.CharField(max_length=1337)
    delay_date = models.CharField(max_length=1337, null=True)
    eurovoc_descriptors = DictField()
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

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]


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


class WrittenQuestionBulletin(models.Model, Jsonify):
    lachambre_id = models.CharField(max_length=1337)
    date = models.CharField(max_length=1337)
    publication_date = models.CharField(max_length=1337)
    url = models.URLField(null=True)
    pdf_url = models.URLField()
    legislature = models.CharField(max_length=1337)
    done = models.BooleanField(default=False)

    class Meta:
        ordering = ["lachambre_id"]

    class MongoMeta:
        indexes = [
            [("lachambre_id", 1)]
        ]


class AnnualReport(models.Model, Jsonify):
    title = DictField()
    date = models.CharField(max_length=1337)
    law_and_article = DictField()
    periodicity = models.CharField(max_length=1337)
    pdf_url = models.URLField()

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

from json import dumps
from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField, DictField

LACHAMBRE_PREFIX="http://www.lachambre.be/kvvcr/"

class Jsonify(object):
    def json(self):
        return dumps(self.__class__.objects.filter(pk=self.pk).values()[0], indent=4)

class Deputy(models.Model, Jsonify):
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
    cv = models.CharField(max_length=1337)
    commissions = ListField(EmbeddedModelField('CommissionMembership'))

    documents_principal_author_url = models.URLField()
    documents_principal_author_list = ListField(EmbeddedModelField('Document'))
    documents_principal_signator_url = models.URLField()
    documents_principal_signator_list = ListField(EmbeddedModelField('Document'))

    documents_next_author_url = models.URLField()
    documents_next_author_list = ListField(EmbeddedModelField('Document'))
    documents_next_signator_url = models.URLField()
    documents_next_signator_list = ListField(EmbeddedModelField('Document'))

    documents_rapporter_url = models.URLField()
    documents_rapporter_list = ListField(EmbeddedModelField('Document'))

    questions_written_url = models.URLField()
    questions_written_list = ListField(EmbeddedModelField('WrittenQuestion'))

    questions_oral_plenary_url = models.URLField()
    questions_oral_plenary_list = ListField(EmbeddedModelField('Question'))

    questions_oral_commission_url = models.URLField()
    questions_oral_commission_list = ListField(EmbeddedModelField('Question'))

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

class Party(models.Model, Jsonify):
    name = models.CharField(max_length=1337)
    url = models.URLField()

    def __unicode__(self):
        return self.name


class CommissionMembership(models.Model, Jsonify):
    role = models.CharField(max_length=1337)
    commission = models.ForeignKey("Commission")
    deputy = models.ForeignKey("Deputy")


class Commission(models.Model, Jsonify):
    lachambre_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=1337)
    full_name = models.CharField(max_length=1337)
    url = models.URLField()
    type = models.CharField(max_length=1337)
    deputies = ListField(models.ForeignKey(CommissionMembership))
    seats = DictField()


class Document(models.Model, Jsonify):
    title = models.CharField(max_length=1337)
    url = models.CharField(max_length=1337)
    full_details_url = models.CharField(max_length=1337)
    status_chambre = models.CharField(max_length=1337, null=True)
    status_senat = models.CharField(max_length=1337, null=True)
    eurovoc_main_descriptor = models.CharField(max_length=1337, null=True)
    deposition_date = models.CharField(max_length=1337, null=True)
    constitution_article = models.CharField(max_length=1337)
    in_charge_commissions = ListField(EmbeddedModelField('InChargeCommissions'))
    plenaries = ListField(EmbeddedModelField('DocumentPlenary'))
    senat_plenaries = ListField(EmbeddedModelField('DocumentSenatPlenary'))
    timeline = ListField(EmbeddedModelField('DocumentTimeLine'))
    eurovoc_descriptors = ListField()
    eurovoc_candidats_descriptors = ListField()
    keywords = ListField()
    lachambre_id = models.IntegerField(unique=True)
    analysis = EmbeddedModelField('Analysis', null=True)
    document_chambre = EmbeddedModelField('DocumentChambre', null=True)
    document_senat = EmbeddedModelField('DocumentSenat', null=True)
    vote_date = models.CharField(max_length=1337)
    vote_senat_date = models.CharField(max_length=1337)
    law_date = models.CharField(max_length=1337)
    moniteur_number = models.CharField(max_length=1337)
    moniteur_date = models.CharField(max_length=1337)
    main_docs = ListField()
    candidature_vote_date = models.CharField(max_length=1337)

    def __unicode__(self):
        return "%s - %s" % (self.lachambre_id, self.title)

    def get_url(self):
        return LACHAMBRE_PREFIX + self.url if not self.url.startswith("http") else self.url


class InChargeCommissions(models.Model):
    visibility = models.CharField(max_length=1337)
    # need to turn that into a EmbeddedModelField(commissions) in the futur
    # when the commissions will be parsed
    commission = models.CharField(max_length=1337)
    rapporters = ListField()
    agenda = ListField()
    incident = ListField()
    rapport = DictField()


class DocumentPlenary(models.Model):
    visibility = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)
    agenda = ListField()
    incident = ListField()


class DocumentSenatPlenary(models.Model):
    visibility = models.CharField(max_length=1337)
    agenda = ListField()


class DocumentChambre(models.Model):
    deposition_date = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)
    taken_in_account_date = models.CharField(max_length=1337)
    distribution_date = models.CharField(max_length=1337)
    sending_date = models.CharField(max_length=1337)
    ending_date = models.CharField(max_length=1337)
    status = models.CharField(max_length=1337)
    authors = ListField()
    comments = ListField()
    pdf = EmbeddedModelField('DocumentChambrePdf')
    other_pdfs = ListField(EmbeddedModelField('OtherDocumentChambrePdf'))
    joint_pdfs = ListField()


class DocumentChambrePdf(models.Model):
    url = models.CharField(max_length=1337)
    session = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)


class DocumentSenat(models.Model):
    deposition_date = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)
    comments = ListField()
    ending_date = models.CharField(max_length=1337)
    author = models.CharField(max_length=1337)
    pdf = EmbeddedModelField('DocumentSenatPdf')
    comments = ListField()
    status = models.CharField(max_length=1337)
    other_pdfs = ListField(EmbeddedModelField('OtherDocumentSenatPdf'))


class DocumentSenatPdf(models.Model):
    url = models.CharField(max_length=1337)
    session = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)


class OtherDocumentSenatPdf(models.Model):
    url = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)
    date = models.CharField(max_length=1337)
    authors = ListField()


class OtherDocumentChambrePdf(models.Model):
    url = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337)
    distribution_date = models.CharField(max_length=1337)
    authors = ListField()


class DocumentTimeLine(models.Model):
    title = models.CharField(max_length=1337)
    date = models.CharField(max_length=1337)


class WrittenQuestion(models.Model, Jsonify):
    title = models.CharField(max_length=1337)
    departement = models.CharField(max_length=1337, )
    eurovoc_descriptors = ListField()
    deposition_date = models.CharField(max_length=1337, )
    delay_date = models.CharField(max_length=1337, null=True)
    keywords = ListField()
    url = models.URLField()
    lachambre_id = models.CharField(max_length=1337)

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

class Analysis(models.Model, Jsonify):
    title = models.CharField(max_length=1337)
    descriptor = models.CharField(max_length=1337)
    url = models.URLField()
    type = models.CharField(max_length=1337)
    lachambre_id = models.CharField(max_length=1337)

class WrittenQuestionBulletin(models.Model, Jsonify):
    lachambre_id = models.CharField(max_length=1337)
    date = models.CharField(max_length=1337)
    publication_date = models.CharField(max_length=1337)
    url = models.URLField()
    pdf_url = models.URLField()
    legislature = models.CharField(max_length=1337)

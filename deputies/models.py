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
from djangotoolbox.fields import ListField, EmbeddedModelField

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
    name = models.CharField(max_length=1337)
    role = models.CharField(max_length=1337)
    url = models.URLField()
    commission = models.ForeignKey('Commission')

class Commission(models.Model, Jsonify):
    lachambre_id = models.IntegerField(unique=True)

class Document(models.Model, Jsonify):
    title = models.CharField(max_length=1337)
    url = models.CharField(max_length=1337)
    full_details_url = models.CharField(max_length=1337)
    status_chambre = models.CharField(max_length=1337, null=True)
    status_senat = models.CharField(max_length=1337, null=True)
    eurovoc_main_descriptor = models.CharField(max_length=1337, null=True)
    deposition_date = models.CharField(max_length=1337, null=True)
    constitution_article = models.CharField(max_length=1337)
    visibility = models.CharField(max_length=1337)
    # need to turn that into a EmbeddedModelField(commissions) in the futur
    # when the commissions will be parsed
    commissions = ListField()
    timeline = ListField(EmbeddedModelField('DocumentTimeLine'))
    eurovoc_descriptors = ListField()
    keywords = ListField()
    lachambre_id = models.IntegerField(unique=True)

    def __unicode__(self):
        return "%s - %s" % (self.lachambre_id, self.title)


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
    session_id = models.CharField(max_length=1337, )
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

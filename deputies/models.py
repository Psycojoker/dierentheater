from json import dumps
from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField

class Jsonify(object):
    def json(self):
        return dumps(self.__class__.objects.filter(pk=self.pk).values()[0], indent=4)

class Deputy(models.Model, Jsonify):
    full_name = models.CharField(max_length=1337, unique=True)
    emails = ListField()
    party = models.ForeignKey('Party')
    url = models.CharField(max_length=1337)
    websites = ListField()
    lachambre_id = models.CharField(max_length=1337, unique=True)
    language = models.CharField(max_length=1337)
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
    questions_written_list = ListField(EmbeddedModelField('Question'))

    questions_oral_plenary_url = models.URLField()
    questions_oral_plenary_list = ListField(EmbeddedModelField('Question'))

    questions_oral_commission_url = models.URLField()
    questions_oral_commission_list = ListField(EmbeddedModelField('Question'))

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

    class Meta:
        ordering = ['full_name']


class Party(models.Model, Jsonify):
    name = models.CharField(max_length=1337)
    url = models.URLField()

    def __unicode__(self):
        return self.name


class CommissionMembership(models.Model, Jsonify):
    name = models.CharField(max_length=1337)
    role = models.CharField(max_length=1337)
    url = models.URLField()
    lachambre_id = models.IntegerField(unique=True)

class Document(models.Model, Jsonify):
    url = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337, default=None, null=True)
    lachambre_id = models.IntegerField(unique=True)

    class Meta:
        ordering = ['lachambre_id']

class Question(models.Model, Jsonify):
    url = models.URLField()
    type = models.CharField(max_length=1337)
    lachambre_id = models.CharField(max_length=1337)

    class Meta:
        ordering = ['lachambre_id']

class Analysis(models.Model, Jsonify):
    url = models.URLField()
    type = models.CharField(max_length=1337)
    lachambre_id = models.CharField(max_length=1337)

    class Meta:
        ordering = ['lachambre_id']

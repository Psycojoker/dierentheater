from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField

class Deputy(models.Model):
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

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

    class Meta:
        ordering = ['full_name']


class Party(models.Model):
    name = models.CharField(max_length=1337)
    url = models.URLField()

    def __unicode__(self):
        return self.name


class CommissionMembership(models.Model):
    name = models.CharField(max_length=1337)
    role = models.CharField(max_length=1337)
    url = models.URLField()

class Document(models.Model):
    url = models.CharField(max_length=1337)
    type = models.CharField(max_length=1337, default=None, null=True)

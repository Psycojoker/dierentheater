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
    documents_principal_author_list = ListField(EmbeddedModelField('MainDocument'))

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

class MainDocument(models.Model):
    url = models.CharField(max_length=1337)

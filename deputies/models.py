from django.db import models
from djangotoolbox.fields import ListField

class Deputy(models.Model):
    full_name = models.CharField(max_length=1337, unique=True)
    emails = ListField()
    party = models.ForeignKey('Party')
    url = models.CharField(max_length=1337)
    websites = ListField()
    lachambre_id = models.CharField(max_length=1337, unique=True)

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

class Party(models.Model):
    name = models.CharField(max_length=1337)
    url = models.URLField()

    def __unicode__(self):
        return self.name

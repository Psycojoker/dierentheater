from django.db import models
from djangotoolbox.fields import ListField

class Deputy(models.Model):
    full_name = models.CharField(max_length=1337, unique=True)
    emails = ListField()
    party = models.ForeignKey('Party')
    url = models.CharField(max_length=1337)
    websites = ListField()
    lachambre_id = models.CharField(max_length=1337, unique=True)
    language = models.CharField(max_length=1337)
    cv = models.CharField(max_length=1337)

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

    class Meta:
        ordering = ['full_name']


class Party(models.Model):
    name = models.CharField(max_length=1337)
    url = models.URLField()

    def __unicode__(self):
        return self.name

from django.db import models
from djangotoolbox.fields import ListField

class Deputy(models.Model):
    full_name = models.CharField(max_length=1337)
    emails = ListField()
    party_name = models.CharField(max_length=1337)
    party_url = models.CharField(max_length=1337)
    #lachambre_id = models.IntegerField(max_length=1337)
    #first_name = models.CharField(max_length=1337)
    #last_name = models.CharField(max_length=1337)
    #websites = ListField()

    def __unicode__(self):
        return '%s - %s' % (self.full_name, self.party)

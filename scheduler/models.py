from datetime import datetime
from django.db import models
from djangotoolbox.fields import ListField

class Task(models.Model):
    function = models.CharField(max_length=1337)
    args = ListField()
    datetime = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return "%s(%s)" % (self.function, ", ".join(self.args))

    class Meta:
        ordering = ["datetime"]

    class MongoMeta:
        indexes = [
            [("datetime", 1)]
        ]

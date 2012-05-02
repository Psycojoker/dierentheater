import logging
logger = logging.getLogger('')

from django.db import models
from djangotoolbox.fields import EmbeddedModelField

from utils import irc


def history(klass):
    def save(self, *args, **kwargs):
        in_db = self.__class__.objects.filter(id=self.id)
        if not in_db:
            if hasattr(self, "get_url"):
                irc(u"[NEW] %s - %s".encode("Utf-8") % (self, self.get_url().encode("Utf-8")))
            else:
                irc(u"[NEW] %s".encode("Utf-8") % self)
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
            if hasattr(self, "get_url"):
                irc(u"[MODIFIED] %s - %s".encode("Utf-8") % (self, self.get_url().encode("Utf-8")))
            else:
                irc(u"[MODIFIED] %s".encode("Utf-8") % self)

        return models.Model.save(self, *args, **kwargs)

    klass.save = save
    return klass


class HistoryManager(models.Manager):
    def get_query_set(self):
        return super(HistoryManager, self).get_query_set().filter(current=True)


def diff(row, other):
    if row.__class__ != other.__class__:
        return True

    for field in map(lambda x: x.attname, row._meta.fields):
        if not isinstance(field, (EmbeddedModelField)):
            print type(getattr(row, field)), getattr(row, field)
            if not isinstance(getattr(row, field), (models.Model, list)):
                if getattr(row, field) != getattr(other, field):
                    logger.info("[%s] '%s' != '%s'" % (field, getattr(row, field), getattr(other, field)))
                    return True
            elif isinstance(getattr(row, field), list):
                for i, j in zip(getattr(row, field), getattr(row, field)):
                    if not isinstance(i, models.Model):
                        if i != j:
                            return True
                    else:
                        if diff(i, j):
                            return True
            else:
                if diff(getattr(row, field), getattr(other, field)):
                    return True

    return False

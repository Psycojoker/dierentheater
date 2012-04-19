from time import sleep

from lachambre.models import Document

from tasks import *


def reparse_all_documents():
    for document in Document.objects.all():
        send("parse_a_document;%s" % document.lachambre_id)
        sleep(30)

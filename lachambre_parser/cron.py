from time import sleep

from scheduler import send
from lachambre.models import Document

def test():
    send("pouet")

def check_for_new_documents():
    send("check_for_new_documents")

def reparse_all_documents():
    for document in Document.objects.all():
        send("parse_a_document;%s" % document.lachambre_id)
        sleep(30)

def reparse_all_deputies():
    send("scrape")

def check_for_new_deputies():
    send("check_for_new_deputies")

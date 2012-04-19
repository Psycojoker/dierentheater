from send import send

def check_for_new_documents():
    send("check_for_new_documents")

def reparse_all_documents():
    send("parse_every_documents")

def reparse_all_deputies():
    send("scrape")

def check_for_new_deputies():
    send("check_for_new_deputies")

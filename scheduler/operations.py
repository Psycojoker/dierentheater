from lachambre_parser import documents, deputies

operations = {
    "check_for_new_documents": documents.check_for_new_documents,
    "reparse_all_documents": documents.parse_every_documents,
    "parse_a_document": documents.handle_document,
    "reparse_all_deputies": deputies.scrape,
}

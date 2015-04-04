# encoding: utf-8

from parser_core.utils import clean_text, AccessControlDict


def document_pdf_part_cutter(soup):
    result = []
    blob = [soup('tr')[0]]
    for i in soup('tr')[1:]:
        if not clean_text(i.text):
            continue
        if not i.img or not i.img.get("class") or i.img["class"] != "picto":
            blob.append(i)
        else:
            result.append(blob)
            blob = [i]

    result.append(blob)
    return result


def document_to_dico(table):
    is_pdf_section = lambda i: i.td.img
    is_noise = lambda i: i == u"\n" or i.td.text in ("&#13;", "&nbsp;", "&#160;")
    is_subsection = lambda i: i.td.b
    dico = AccessControlDict()
    sub_section = None
    for i in table:
        if is_noise(i):
            continue
        if is_subsection(i):
            sub_section = _build_sub_section(i, dico)
        elif is_pdf_section(i):
            _build_pdf_sub_section(i, dico, sub_section)
        else:  # is first level
            _build_first_level(i, dico)
    return dico


def _build_sub_section(i, dico):
    sub_section = clean_text(i.td.b.text)
    if dico.get(sub_section):
        raise Exception("'%s' is already use as a key for '%s'" % (sub_section, dico[sub_section]))
    dico[sub_section] = AccessControlDict()
    dico[sub_section]["head"] = i('td')[1]
    return sub_section


def _build_pdf_sub_section(i, dico, sub_section):
    key = clean_text(i.td.text)
    # we can have a list on joined documents
    if unicode(key) in (u'Document(s) joint(s)/lié(s)', u'Gekoppeld(e)/verbonden document(en)'):
        if not dico[sub_section].get(key):
            dico[sub_section][key] = []
        dico[sub_section][key].append(i('td')[1])
    elif dico[sub_section].get(key):
        raise Exception("'%s' is already use as a key in the sub_section '%s' for '%s'" % (key, sub_section, dico[sub_section][key]))
    else:
        dico[sub_section][key] = i('td')[1]


def _build_first_level(i, dico):
    key = clean_text(i.td.text)
    # we can get severals Moniter erratum
    if unicode(key) in ('Moniteur erratum', 'Staatsblad erratum'):
        if not dico.get(key):
            dico[key] = []
        dico[key].append(i('td')[1])
    else:
        if dico.get(key):
            raise Exception("'%s' is already use as a key for '%s'" % (key, dico[key]))
        dico[key] = i('td')[1]

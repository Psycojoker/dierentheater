# -*- coding:Utf-8 -*-

#  Dieren Theater - lachambre.be to json sausage machine
#  Copyright (C) 2012  Laurent Peuch <cortex@worlddomination.be>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from utils import clean_text,\
                  AccessControlDict

def document_to_dico(table):
    dico = AccessControlDict()
    sub_section = None
    for i in table:
        if i == u"\n" or i.td.text in ("&#13;", "&nbsp;", "&#160;"):
            continue
        if i.td.b:
            sub_section = build_sub_section(i, dico)
        elif i.td.img:
            build_pdf_sub_section(i, dico, sub_section)
        else:
            build_first_level(i, dico)
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
    if unicode(key) == u'Document(s) joint(s)/lié(s)':
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
    if unicode(key) == 'Moniteur erratum':
        if not dico.get(key):
            dico[key] = []
        dico[key].append(i('td')[1])
    else:
        if dico.get(key):
            raise Exception("'%s' is already use as a key for '%s'" % (key, dico[key]))
        dico[key] = i('td')[1]


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

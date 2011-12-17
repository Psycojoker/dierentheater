#!/usr/bin/python
# -*- coding:Utf-8 -*-

#  Dieren Theater - lachambre.be to json sausage machine
#  Copyright (C) 2011  Laurent Peuch <cortex@worlddomination.be>
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

import os
import re
from json import dumps
from json_diff import Comparator
from StringIO import StringIO

SEPARATOR = "-------------------------------------------------------------------------------------------------------------------------------"

def pdf_to_text(pdf_name):
    os.system("pdftotext -layout %s" % pdf_name)
    return open(pdf_name.replace(".pdf", ".txt"), "r").read()

def remove_useless_informations(text):
    result = []
    for i in text.split("\n")[1:]:
        if "DOC 53" in i:
            continue
        if "\x0c" in i:
            continue
        if re.match("^CHAMBRE .* ZITTINGSPERIODE$", i):
            continue
        if re.match("^ *\d\d\d\d *$", i):
            continue
        if "Imprimerie centrale – Cette publication est imprimée exclusivement sur du papier certiﬁé FSC" in i:
            continue
        if "Centrale drukkerij – Deze publicatie wordt uitsluitend gedrukt op FSC gecertiﬁceerd papier" in i:
            continue
        if "Publications ofﬁcielles éditées par la Chambre des représentants" in i:
            continue
        else:
            result.append(i)
    return "\n".join(result)

def strip(text):
    work = text.split("\n")
    a = 0
    while re.match("^ *$", work[a]):
        a += 1

    b = 0
    while re.match("^ *$", work[b]):
        b += 1

    return "\n".join(text.split("\n")[a:-b])

def horizontal_split(text):
    result = [[]]
    blank_line = 0
    for i in text.split("\n"):
        if i.strip():
            result[-1].append(i)
        else:
            blank_line += 1
            if blank_line == 3:
                result.append([])
                blank_line = 0
    return filter(None, result)

def remove_useless_blocks(text):
    # first one is "La Chambre blablabla"
    # second one is the date, we have it on the website
    # last one is the authors, also on the website
    text = text[2:-1]
    # author name, also on the website
    if "SAMENVATTING" not in text[1][0]:
        text.pop(1)
    return text

def split_horizontally(block):
    if not block:
        return [], []

    left, right = [], []

    split_size = 2

    searchable_area = filter(lambda x: len(filter(lambda x: x.strip(), x.split("   "))) == 2, block[:])
    searchable_area = map(lambda x: x.decode("Utf-8"), searchable_area)
    split_index = 7
    good = False
    while not good:
        for i in searchable_area:
            if i[split_index:split_index+2] != "  ":
                split_index += 1
                break
        else:
            good = True
        if split_index > max(map(lambda x: len(x), searchable_area)):
            raise Exception

    for i in map(lambda x: x.decode("Utf-8"), block):
        if len(filter(lambda x: x.strip(), i.split(" "*split_size))) == 2:
            left.append(i[:split_index])
            right.append(i[split_index+2:])
        else:
            left.append(i.rstrip())

    return map(lambda x: x.encode("Utf-8"), left), map(lambda x: x.encode("Utf-8"), right)

def rebuild_paragraphe(block):
    # '-' are at the end of a line when a word is split in two
    # after " ".join we have some "- " resulting of the join of 2 parts of a word
    # remove them
    return " ".join(map(lambda x: x.strip(), block)).replace("- ", "")

def parse_abstract(abstract):
    # first line is useless
    abstract[0] = abstract[0].lower().strip()
    return map(lambda x: x.capitalize() + ".", map(rebuild_paragraphe, split_horizontally(abstract)))

def left_egualize(block):
    while False not in map(lambda x: x[0] == " ", block):
        block = map(lambda x: x[1:], block)
    return block

def split_raw_paragraph(block):
    block = left_egualize(block)
    result = [[]]
    for i in block:
        if i.startswith("  ") and result != [[]]:
            result.append([])
        result[-1].append(i)
    return result

def parse_two_columns_text(text):
    return map(lambda x: map(rebuild_paragraphe, x), map(split_raw_paragraph, split_horizontally(text)))

def prepare_document(pdf_name):
    text = pdf_to_text(pdf_name)
    text = remove_useless_informations(text)
    text = strip(text)
    text = horizontal_split(text)
    text = remove_useless_blocks(text)
    return text

def is_party_list(block):
    for i in block:
        if ":" not in i:
            return False
    return True

def flaten_list(a_list):
    flat = []
    for i in a_list:
        for j in i:
            flat.append(j)
    return flat

def intelligent_parse(pdf_name):
    def store(key, data):
        document["FR"][key] = data[0]
        document["NL"][key] = data[1]

    text = prepare_document(pdf_name)
    document = {"FR": {}, "NL": {}}

    # abstract is always the first one
    abstract = parse_abstract(text[0])
    store("abstract", abstract)

    # remove abstract
    text.pop(0)

    # if we have a summary
    if "SAMENVATTING" in text[0][0]:
        text.pop(0)
        summary = map(rebuild_paragraphe, split_horizontally(text[0]))
        store("summary", summary)
        text.pop(0)

    if is_party_list(text[0]):
        # if it's the party list, we will have the abbreviations and address also
        # and we don't care about those
        text = text[3:]

    if "TOELICHTING" in text[0][0]:
        text.pop(0)
        development = []
        while "PROPOSITION DE LOI" not in text[0][0]:
            development.append(text.pop(0))

        # remove author signature
        development.pop()
        store("development", map(flaten_list, zip(*map(parse_two_columns_text, development))))

    if "PROPOSITION DE LOI" in text[0][0]:
        text.pop(0)
        store("articles", map(flaten_list, zip(*map(parse_two_columns_text, text))))

    return document

def custom_parse(pdf_name):
    text = prepare_document(pdf_name)
    for i in parse_abstract(text[0]):
        print SEPARATOR
        print i
    # text[1] is "RESUMER ..."
    for i in map(rebuild_paragraphe, split_horizontally(text[2])):
        print SEPARATOR
        print i
    # text[3] is party list
    # text[4] is abbrevations
    # text[5] is la chambre's address
    # text[6] is "DÉVELOPPEMENTS ..."
    for x in text[7:14]:
        print SEPARATOR
        for i in parse_two_columns_text(x):
            for j in i:
                print SEPARATOR
                print j
    # text[15] is the authors
    # text[16] is "PROPOSITION DE LOI ..."
    for i in parse_two_columns_text(text[17]):
        for j in i:
            print SEPARATOR
            print j
    for i in parse_two_columns_text(text[18]):
        for j in i:
            print SEPARATOR
            print j

if __name__ == "__main__":
    #custom_parse("53K1961001.pdf")
    assert not Comparator(StringIO(dumps(intelligent_parse("53K1961001.pdf"))), open("testing", "r")).compare_dicts()

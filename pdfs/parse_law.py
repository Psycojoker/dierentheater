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
    text.pop(1)
    return text

def split_horizontally(block):
    left, right = [], []

    # get the biggest withespace I can find in all sentences
    split_size = 10
    while False in map(lambda x: len(x) >= 2, map(lambda x: x.split(" "*split_size), filter(lambda x: len(x.split("  ")) >= 2, block))):
        split_size -= 1

    # start to search at 1/4 index of the avg len of every sentences
    split_index = (sum(map(lambda x: len(x), block)) / len(block)) / 4
    for i in block:
        if len(filter(lambda x: x.strip(), i.split(" "*split_size))) == 2:
            z = split_index
            while i[z:z + split_size] != " "*split_size:
                z += 1
                if z == len(i):
                    raise Exception
            left.append(i[:z])
            right.append(i[z+split_size:])
        else:
            left.append(i.rstrip())

    return left, right

def rebuild_paragraphe(block):
    block = map(lambda x: x[:-1] if x[-1] == "-" else x, block)
    return " ".join(map(lambda x: x.strip(), block))

def parse_abstract(abstract):
    # first line is useless
    abstract[0] = abstract[0].lower().strip()
    return map(lambda x: x.capitalize() + ".", map(rebuild_paragraphe, split_horizontally(abstract)))

def parse(pdf_name):
    text = pdf_to_text(pdf_name)
    text = remove_useless_informations(text)
    text = strip(text)
    text = horizontal_split(text)
    text = remove_useless_blocks(text)
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
    for i in text[5:]:
        print SEPARATOR
        print "\n".join(i)

if __name__ == "__main__":
    parse("53K1961001.pdf")

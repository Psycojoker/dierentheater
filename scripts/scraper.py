# -*- coding:Utf-8 -*-

#  Dieren Theater - lachambre.be to json sausage machine
#  Copyright (C) 2011-12  Laurent Peuch <cortex@worlddomination.be>
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

from lachambre_parser.reports import annual_reports
from lachambre_parser.commissions import commissions
from lachambre_parser.written_questions import written_questions
from lachambre_parser.documents import documents
from lachambre_parser.deputies import deputies_list, deputies

from deputies.models import Deputy,\
                            Party,\
                            CommissionMembership,\
                            Document,\
                            Question,\
                            Analysis,\
                            Commission,\
                            WrittenQuestion,\
                            DocumentTimeLine,\
                            DocumentChambre,\
                            DocumentChambrePdf,\
                            OtherDocumentChambrePdf,\
                            DocumentSenat,\
                            DocumentSenatPdf,\
                            InChargeCommissions,\
                            DocumentPlenary,\
                            DocumentSenatPlenary,\
                            OtherDocumentSenatPdf,\
                            WrittenQuestionBulletin,\
                            AnnualReport


def clean():
    print "cleaning db"
    map(lambda x: x.objects.all().delete(), (Deputy, Party, CommissionMembership, Document, Question, Analysis, Commission, WrittenQuestion, DocumentTimeLine, DocumentChambre, DocumentChambrePdf, DocumentSenat, DocumentSenatPdf, InChargeCommissions, DocumentPlenary, DocumentSenatPlenary, OtherDocumentSenatPdf, WrittenQuestionBulletin, AnnualReport, OtherDocumentChambrePdf))


def run():
    clean()
    deputies_list()
    commissions()
    deputies()
    documents()
    written_questions()
    annual_reports()

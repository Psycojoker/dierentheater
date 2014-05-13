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

import logging
logger = logging.getLogger('')
logger.handlers[1].setLevel(logging.DEBUG)

from optparse import make_option
from django.core.management.base import BaseCommand

from lachambre_parser import reports
from lachambre_parser import commissions
from lachambre_parser import written_questions
from lachambre_parser import documents
from lachambre_parser import deputies


parsers = {
    'reports': reports,
    'commissions': commissions,
    'written_questions': written_questions,
    'documents': documents,
    'deputies': deputies,
}

class Command(BaseCommand):
    option_list = BaseCommand.option_list + tuple(
        make_option('--%s' % x,
            action='store_true',
            dest='%s' % x,
            default=False,
            help='Parse %s' % x)
        for x in parsers.keys()
    )

    def handle(self, *args, **options):
        parsers_to_run = filter(lambda x: options[x], parsers.keys())
        if not parsers_to_run:
            parsers_to_run = parsers.values()
        else:
            parsers_to_run = [parsers[x] for x in parsers_to_run]

        if deputies in parsers_to_run:
            deputies.deputies_list()

        for parser in parsers:
            parser.scrape()

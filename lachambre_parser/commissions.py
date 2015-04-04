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

import logging
logger = logging.getLogger('')

from lachambre.models import Commission, CommissionMembership


def clean_models():
    logger.debug("cleaning commissions modèles")
    map(lambda x: x.objects.all().delete(), (CommissionMembership, Commission))


def scrape():
    Commission.fetch_list()

#  lachambre.be to json sausage machine
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

from os import system, makedirs
from os.path import exists
from django.conf import settings

STATIC_FOLDER = settings.PROJECT_PATH + "/lachambre/static/dumps/"
MODELS = ("annualreport", "commission", "deputy", "document", "writtenquestion", "commissionmembership")

OBDL = """\
This DATABASE is made available under the Open Database License:
http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
contents of the database are licensed under the Database Contents License:
http://opendatacommons.org/licenses/dbcl/1.0/"""

def dump_db():
    if not exists(STATIC_FOLDER):
        makedirs(STATIC_FOLDER)
    db = settings.DATABASES["default"]["NAME"]
    for model in MODELS:
        print "mongoexport -d %s -c lachambre_%s --jsonArray > %s%s" % (db, model, STATIC_FOLDER, model)
        system("mongoexport -d %s -c lachambre_%s --jsonArray > %s%s" % (db, model, STATIC_FOLDER, model))

    print "XZing..."
    for model in MODELS:
        print "  %s" % model
        system("cd %s && if [ -e %s.xz ]; then rm %s.xz; fi && xz %s" %(STATIC_FOLDER, model, model, model))
    print "done"
    open("%s/LICENCE" % STATIC_FOLDER, "w").write(OBDL)

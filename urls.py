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

from django.conf.urls.defaults import patterns, include, url
from django.views.generic import TemplateView

from tastypie.api import Api
from lachambre.api import DeputyResource, CommissionMembershipRessource, CommissionResource, DocumentResource, WrittenQuestionResource

v1_api = Api(api_name='v1')
v1_api.register(DeputyResource())
v1_api.register(CommissionResource())
v1_api.register(CommissionMembershipRessource())
v1_api.register(DocumentResource())
v1_api.register(WrittenQuestionResource())

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),
    url(r'^lachambre/', include('lachambre.urls', namespace='deputies')),
    url(r'^api/', include(v1_api.urls)),
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # url(r'^admin/', include(admin.site.urls)),
)

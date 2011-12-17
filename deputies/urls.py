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

from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView, DetailView

from models import Deputy, Commission, Document, Question, Analysis

urlpatterns = patterns('',
    url(r'^deputy/$', ListView.as_view(model=Deputy), name='deputy-list'),
    url(r'^deputy/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Deputy), name='deputy'),
    url(r'^commission/$', ListView.as_view(model=Commission), name='commission-list'),
    url(r'^commission/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Commission), name='commission'),
    url(r'^document/$', ListView.as_view(model=Document), name='document-list'),
    url(r'^document/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Document), name='document'),
    url(r'^question/$', ListView.as_view(model=Question), name='question-list'),
    url(r'^question/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Question), name='question'),
    url(r'^analysis/$', ListView.as_view(model=Analysis), name='analysis-list'),
    url(r'^analysis/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Analysis), name='analysis'),
)

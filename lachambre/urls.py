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

from models import Deputy, Commission, Document, Question, Analysis, WrittenQuestion, AnnualReport

urlpatterns = patterns('',
    url(r'^deputy/$', ListView.as_view(model=Deputy), name='deputy-list'),
    # yes, O in the regex, one deputy has an O instead of a 0 in it's lachambre_id, yes this is awfull
    url(r'^deputy/(?P<slug>[O0-9]+)/$', DetailView.as_view(model=Deputy, slug_field="lachambre_id"), name='deputy'),
    url(r'^commission/$', ListView.as_view(model=Commission), name='commission-list'),
    url(r'^commission/(?P<slug>[0-9]+)/$', DetailView.as_view(model=Commission, slug_field="lachambre_id"), name='commission'),
    url(r'^document/$', ListView.as_view(model=Document), name='document-list'),
    url(r'^document/(?P<slug>[0-9]+)/$', DetailView.as_view(model=Document, slug_field="lachambre_id"), name='document'),
    url(r'^written-question/$', ListView.as_view(model=WrittenQuestion), name='written-question-list'),
    url(r'^written-question/(?P<slug>[-a-zA-Z0-9]+)/$', DetailView.as_view(model=WrittenQuestion, slug_field="lachambre_id"), name='written-question'),
    url(r'^question/$', ListView.as_view(model=Question), name='question-list'),
    url(r'^question/(?P<slug>[A-Z0-9]+)/$', DetailView.as_view(model=Question, slug_field="lachambre_id"), name='question'),
    url(r'^analysis/$', ListView.as_view(model=Analysis), name='analysis-list'),
    url(r'^analysis/(?P<slug>[A-Z0-9]+)/$', DetailView.as_view(model=Analysis, slug_field="lachambre_id"), name='analysis'),
    url(r'^annual-report/$', ListView.as_view(model=AnnualReport), name='annual-report-list'),
    url(r'^annual-report/(?P<pk>[-a-zA-Z0-9]+)/$', DetailView.as_view(model=AnnualReport), name='annual-report'),
)

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

from models import Deputy, Commission, Document, Question, Analysis, WrittenQuestion, AnnualReport, CommissionMembership

urlpatterns = patterns('',
    url(r'^deputy/$', ListView.as_view(queryset=Deputy.objects.all()), name='deputy-list'),
    # yes, O in the regex, one deputy has an O instead of a 0 in it's lachambre_id, yes this is awfull
    url(r'^deputy/(?P<slug>[O0-9]+)/$', DetailView.as_view(queryset=Deputy.objects.all(), slug_field="lachambre_id"), name='deputy'),
    url(r'^commission/$', ListView.as_view(queryset=Commission.objects.all()), name='commission-list'),
    url(r'^commission/(?P<slug>[0-9]+)/$', DetailView.as_view(queryset=Commission.objects.all(), slug_field="lachambre_id"), name='commission'),
    url(r'^commission-membership/$', ListView.as_view(queryset=CommissionMembership.objects.all()), name='commission-membership-list'),
    url(r'^commission-membership/(?P<pk>[-a-zA-Z0-9]+)/$', DetailView.as_view(queryset=CommissionMembership.objects.all()), name='commission-membership'),
    url(r'^document/$', ListView.as_view(queryset=Document.objects.all()), name='document-list'),
    url(r'^document/(?P<slug>[0-9]+)/$', DetailView.as_view(queryset=Document.objects.all(), slug_field="lachambre_id"), name='document'),
    url(r'^written-question/$', ListView.as_view(queryset=WrittenQuestion.objects.all()), name='written-question-list'),
    url(r'^written-question/(?P<slug>[-a-zA-Z0-9]+)/$', DetailView.as_view(queryset=WrittenQuestion.objects.all(), slug_field="lachambre_id"), name='written-question'),
    url(r'^question/$', ListView.as_view(queryset=Question.objects.all()), name='question-list'),
    url(r'^question/(?P<slug>[A-Z0-9]+)/$', DetailView.as_view(queryset=Question.objects.all(), slug_field="lachambre_id"), name='question'),
    url(r'^analysis/$', ListView.as_view(queryset=Analysis.objects.all()), name='analysis-list'),
    url(r'^analysis/(?P<slug>[A-Z0-9]+)/$', DetailView.as_view(queryset=Analysis.objects.all(), slug_field="lachambre_id"), name='analysis'),
    url(r'^annual-report/$', ListView.as_view(queryset=AnnualReport.objects.all()), name='annual-report-list'),
    url(r'^annual-report/(?P<pk>[-a-zA-Z0-9]+)/$', DetailView.as_view(queryset=AnnualReport.objects.all()), name='annual-report'),
)

from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView, DetailView

from models import Deputy, Document

urlpatterns = patterns('',
    url(r'^deputy/$', ListView.as_view(model=Deputy), name='deputy-list'),
    url(r'^deputy/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Deputy), name='deputy'),
    url(r'^document/$', ListView.as_view(model=Document), name='document-list'),
    url(r'^document/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Document), name='document'),
)

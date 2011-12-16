from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView, DetailView

from models import Deputy

urlpatterns = patterns('',
    url(r'^deputy/$', ListView.as_view(model=Deputy), name='list'),
    url(r'^deputy/(?P<pk>[a-z0-9]+)/$', DetailView.as_view(model=Deputy), name='deputy'),
)

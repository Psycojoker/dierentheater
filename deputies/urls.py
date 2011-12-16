from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView

from models import Deputy

urlpatterns = patterns('',
    url(r'^deputy/$', ListView.as_view(model=Deputy), name='list'),
)

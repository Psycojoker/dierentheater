from django.conf.urls.defaults import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # url(r'^admin/', include(admin.site.urls)),
)

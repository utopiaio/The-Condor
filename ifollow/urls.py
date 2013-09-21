from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from front.views import home
admin.autodiscover()

from front.views import contact_us

urlpatterns = patterns('',
    # Examples:
    #url(r'^send_message/$', ClassRooms, name='home'), # change where the view is found or atleast the name son!
    # url(r'^ifollow/', include('ifollow.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^TheCondor/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^TheCondor/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
    url(r'^TheCondor/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),

    url(r'^TheCondor/', include(admin.site.urls)),

    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),
  
    url (r'^contact_us/', contact_us),
    url (r'^.*[/]?', home) # NOTE: even ALL 404's will be replaced by the schools home page -- think this is cool son!
)

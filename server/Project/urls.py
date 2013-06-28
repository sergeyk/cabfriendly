from django.conf.urls.defaults import *
from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('taxi.views',
    # home
    url(r'^$', 'home', name = 'home'),

    # fb stuff
    url(r'^fb_callback/$', 'fb_callback', name = "facebook-callback"),
    url(r'^facebook/login/$', 'facebook_login'),
    url(r'^facebook/logout/$', 'user_logout'),

    # ride list views
    url(r'^rides/current/$', 'current_rides'),
    url(r'^rides/search/$', 'search_rides'),

    # ride search, creation and details
    url(r'^rides/request/$', 'request_ride'),
    # url(r'^rides/new/(?P<sr_id>\d+)/$', 'new_ride'),
    url(r'^rides/new/$', 'new_ride'),
    url(r'^rides/(?P<ride_id>\d+)/$', 'ride_info'),
    url(r'^rides/(?P<ride_id>\d+)/(?P<sr_id>\d+)/$', 'ride_info'),
    url(r'^rides/join/(?P<ride_id>\d+)/$', 'join_ride'),
    url(r'^rides/drop/(?P<ride_id>\d+)/$', 'drop_ride'),
                       
    url(r'^test/(?P<fb_id>\d+)/$', 'facebook_test_login'),
    url(r'^test/all/$', 'all_rides'),

)

# urlpatterns = patterns('taxi.views',
#         url(r'taxi/', 'index'),
#         url(r'testform/', 'contact_form'),
#         url(r'fb/', 'canvas'),
# )

urlpatterns += patterns('',
    # Example:
    #(r'^Project/', include('Project.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

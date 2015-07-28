# vim: set tw=0:

from django.conf.urls import patterns, url, include
from django.conf import settings
from django.views.generic.base import RedirectView
from editorsnotes.main.views.auth import CustomBrowserIDVerify

# API
urlpatterns = patterns('',
    url(r'^', include('editorsnotes.api.urls', namespace='api', app_name='api')),
    url(r'^api/metadata/topics/types/$', 'editorsnotes.api.views.topics.topic_types'),
)

# Auth
urlpatterns += patterns('',
    url(r'^auth/', include('editorsnotes.auth.urls', namespace='auth', app_name='auth')),
)

# The rest
urlpatterns += patterns('',
    url(r'^', include('editorsnotes.other_urls')),
)

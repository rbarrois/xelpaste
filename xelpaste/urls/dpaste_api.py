from django.conf.urls import url, patterns
from ..views import snippet_api

urlpatterns = patterns('',
    url(r'^api/$', snippet_api, name='xelpaste_api_create_snippet'),
)

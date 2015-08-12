from __future__ import absolute_import

from django.conf.urls import url, patterns
from django.conf.urls.static import static

from xelpaste.conf import settings

L = settings.DPASTE_SLUG_LENGTH

urlpatterns = patterns('xelpaste.views',
    url(r'^about/$', 'about', name='xelpaste_about'),

    url(r'^$', 'snippet_new', name='snippet_new'),
    url(r'^upload/$', 'snippet_upload', name='snippet_upload'),
    url(r'^diff/$', 'snippet_diff', name='snippet_diff'),
    url(r'^history/$', 'snippet_history', name='snippet_history'),
    url(r'^delete/$', 'snippet_delete', name='snippet_delete'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/?$' % L, 'snippet_details', name='snippet_details'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/delete/$' % L, 'snippet_delete', name='snippet_delete'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/gist/$' % L, 'snippet_gist', name='snippet_gist'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/raw/?$' % L, 'snippet_details', {'template_name': 'xelpaste/snippet_details_raw.html', 'is_raw': True}, name='snippet_details_raw'),
)
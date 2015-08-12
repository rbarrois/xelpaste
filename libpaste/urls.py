# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import url, patterns

from .conf import settings

L = settings.LIBPASTE_SLUG_LENGTH

urlpatterns = patterns('libpaste.views',
    url(r'^$', 'snippet_new', name='snippet_new'),
    url(r'^upload/$', 'snippet_upload', name='snippet_upload'),
    url(r'^diff/$', 'snippet_diff', name='snippet_diff'),
    url(r'^history/$', 'snippet_history', name='snippet_history'),
    url(r'^delete/$', 'snippet_delete', name='snippet_delete'),
    url(r'^api/$', 'snippet_api', name='api_create_snippet'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/?$' % L, 'snippet_details', name='snippet_details'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/delete/$' % L, 'snippet_delete', name='snippet_delete'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/gist/$' % L, 'snippet_gist', name='snippet_gist'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/raw/?$' % L, 'snippet_details', {'template_name': 'libpaste/snippet_details_raw.html', 'is_raw': True}, name='snippet_details_raw'),
)

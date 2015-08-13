# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import url

from .conf import settings
from . import views

L = settings.LIBPASTE_SLUG_LENGTH

urlpatterns = [
    url(r'^$', views.snippet_new, name='snippet_new'),
    url(r'^upload/$', views.snippet_upload, name='snippet_upload'),
    url(r'^diff/$', views.snippet_diff, name='snippet_diff'),
    url(r'^history/$', views.snippet_history, name='snippet_history'),
    url(r'^delete/$', views.snippet_delete, name='snippet_delete'),
    url(r'^api/$', views.snippet_api, name='api_create_snippet'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/?$' % L, views.snippet_details, name='snippet_details'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/delete/$' % L, views.snippet_delete, name='snippet_delete'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{%d})/raw/?$' % L, views.snippet_details, {'template_name': 'libpaste/snippet_details_raw.html', 'is_raw': True}, name='snippet_details_raw'),
]

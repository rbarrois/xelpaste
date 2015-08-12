# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url, patterns


urlpatterns = patterns('xelpaste.views',
    url(r'^about/$', 'about', name='xelpaste_about'),
    url(r'^', include('libpaste.urls')),
)

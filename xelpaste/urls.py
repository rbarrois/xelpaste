# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^about/$', views.about, name='xelpaste_about'),
    url(r'^', include('libpaste.urls')),
]

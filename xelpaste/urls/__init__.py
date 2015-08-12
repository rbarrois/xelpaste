from __future__ import absolute_import

from django.conf.urls import url, patterns, include

urlpatterns = patterns(
    '',
    url(r'^', include('xelpaste.urls.xelpaste_api')),
    url(r'^', include('xelpaste.urls.xelpaste')),
)

# Custom error handlers which load `xelpaste/<code>.html` instead of `<code>.html`
handler404 = 'xelpaste.views.page_not_found'
handler500 = 'xelpaste.views.server_error'

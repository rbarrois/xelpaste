# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db.models import Count
from django.shortcuts import render
from django.views import defaults as django_defaults

from libpaste import models

# -----------------------------------------------------------------------------
# Static pages
# -----------------------------------------------------------------------------

def about(request, template_name='xelpaste/about.html'):
    """
    A rather static page, we need a view just to display a couple of
    statistics.
    """
    return render(request, template_name, {
        'total': models.Snippet.objects.count(),
        'stats': models.Snippet.objects.values('lexer').annotate(
            count=Count('lexer')).order_by('-count')[:5],
        'page': 'about',
    })


# -----------------------------------------------------------------------------
# Custom 404 and 500 views. Its easier to integrate this as a app if we
# handle them here.
# -----------------------------------------------------------------------------

def page_not_found(request, template_name='xelpaste/404.html'):
    return django_defaults.page_not_found(request, template_name) # pragma: no cover

def server_error(request, template_name='xelpaste/500.html'):
    return django_defaults.server_error(request, template_name) # pragma: no cover

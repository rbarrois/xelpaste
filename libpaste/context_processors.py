# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from libpaste.conf import settings


def libpaste_settings(request):
    return {
        'LIBPASTE_SLUG_LENGTH': settings.LIBPASTE_SLUG_LENGTH,
        'LIBPASTE_BASE_URL': settings.LIBPASTE_BASE_URL,
        'LIBPASTE_SITENAME': settings.LIBPASTE_SITENAME,
    }

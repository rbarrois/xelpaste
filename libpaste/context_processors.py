# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings


def libpaste_settings(request):
    return {
        'LIBPASTE_SLUG_LENGTH': settings.LIBPASTE_SLUG_LENGTH,
        'LIBPASTE_BASE_URL': settings.LIBPASTE_BASE_URL,
        'LIBPASTE_DOMAIN': settings.LIBPASTE_DOMAIN,
    }

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import getconf
import os
import re


# Paths
# =====
BASE_DIR = os.path.dirname(__file__)
CHECKOUT_DIR = os.path.dirname(BASE_DIR)


# Global configuration
# ====================

config = getconf.ConfigGetter('xelpaste', [
    '/etc/xelpaste/*.ini',
    os.path.join(CHECKOUT_DIR, 'local_settings.ini'),
    ])


APPMODE = config.get('app.mode', 'prod')
assert APPMODE in ('dev', 'dist', 'prod'), "Invalid application mode %s" % APPMODE


# Generic Django settings
# =======================

# SECURITY WARNING: keep the secret key used in production secret!
if APPMODE in ('dev', 'dist'):
    _default_secret_key = 'Dev only!!'
else:
    _default_secret_key = ''

SECRET_KEY = config.get('django.secret_key', _default_secret_key)


# Debug
# =====

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.getbool('app.debug', APPMODE == 'dev')
TEMPLATE_DEBUG = DEBUG

if config.get('site.admin_mail'):
    ADMINS = (
        ("Xelpaste admins", config.get('site.admin_mail')),
    )



# URLs
# ====

if APPMODE == 'dev':
    _default_domain = 'example.org'
else:
    _default_domain = ''

ALLOWED_HOSTS = config.getlist('site.allowed_hosts')
LIBPASTE_DOMAIN = config.get('site.domain', _default_domain)
LIBPASTE_BASE_URL = config.get('site.base_url', 'http://%s/' % LIBPASTE_DOMAIN)


# Loadable components
# ===================

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'django.contrib.sessions',

    'mptt',
    'libpaste',
    'xelpaste',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'libpaste.context_processors.libpaste_settings',
)

ROOT_URLCONF = 'xelpaste.urls'

if APPMODE == 'dev':
    # Avoid the need for collectstatic before running tests
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'


# Database
# ========

_ENGINE_MAP = {
    'sqlite': 'django.db.backends.sqlite3',
    'mysql': 'django.db.backends.mysql',
    'postgresql': 'django.db.backends.postgresql_psycopg2',
}
_engine = config.get('db.engine', 'sqlite')
if _engine not in _ENGINE_MAP:
    raise ImproperlyConfigured(
        "DB engine %s is unknown; please choose from %s"
        % (_engine, ', '.join(sorted(_ENGINE_MAP.keys())))
    )
if _engine == 'sqlite':
    if APPMODE == 'dev':
        _default_db_name = os.path.join(CHECKOUT_DIR, 'dev', 'db.sqlite')
    else:
        _default_db_name = '/var/lib/xelpaste/db.sqlite'
else:
    _default_db_name = 'xelpaste'


DATABASES = {
    'default': {
        'ENGINE': _ENGINE_MAP[_engine],
        'NAME': config.get('db.name', _default_db_name),
        'HOST': config.get('db.host'),
        'PORT': config.get('db.port'),
        'USER': config.get('db.user'),
        'PASSWORD': config.get('db.password'),
    }
}

# Internationalization
# ====================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# ======================================

STATIC_URL = config.get('site.assets_url', '/assets/')
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')


# Uploads
# =======

if APPMODE == 'dev':
    _default_media = os.path.join(CHECKOUT_DIR, 'dev', 'media')
else:
    _default_media = ''

MEDIA_ROOT = config.get('uploads.dir', _default_media)
LIBPASTE_UPLOAD_TO = 'snippets'
SENDFILE_BACKEND = 'sendfile.backends.%s' % config.get('uploads.serve', 'simple')
SENDFILE_ROOT = os.path.join(MEDIA_ROOT, LIBPASTE_UPLOAD_TO)
SENDFILE_URL = config.get('uploads.internal_url', '/uploads/')



# Snippets
# ========


def parse_size(size):
    """Parse a size, kinda like 10MB, and return an amount of bytes."""
    size_re = re.compile(r'^(\d+)([GMK]?B)$')
    match = size_re.match(size.upper())
    if not match:
        raise ValueError("Invalid size %r" % size)
    amount, unit = match.groups()
    amount = int(amount)
    if unit == 'GB':
        return amount * 1024 * 1024 * 1024
    elif unit == 'MB':
        return amount * 1024 * 1024
    elif unit == 'kB':
        return amount * 1024
    else:
        return amount


LIBPASTE_MAX_CONTENT_LENGTH = parse_size(config.get('snippets.max_content', '1MB'))
LIBPASTE_MAX_FILE_LENGTH = parse_size(config.get('snippets.max_file', '10MB'))
LIBPASTE_SLUG_LENGTH = config.getint('snippets.slug_length', 6)

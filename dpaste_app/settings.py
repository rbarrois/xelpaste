import getconf
import os
import re


# Paths
# =====
BASE_DIR = os.path.dirname(__file__)
CHECKOUT_DIR = os.path.dirname(BASE_DIR)


# Global configuration
# ====================

config = getconf.ConfigGetter('xelpaste',
    '/etc/xelpaste/settings.ini',
    os.path.join(CHECKOUT_DIR, 'local_settings.ini'),
)


env = config.get('env', 'dev')
assert env in ('dev', 'prod'), "Invalid environment %s" % env


# Generic Django settings
# =======================

# SECURITY WARNING: keep the secret key used in production secret!
if env == 'dev':
    _default_secret_key = 'Dev only!!'
else:
    _default_secret_key = ''

SECRET_KEY = config.get('django.secret_key', _default_secret_key)


# Debug
# =====

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.getbool('dev.debug', env == 'dev')
TEMPLATE_DEBUG = DEBUG

if config.get('dev.admin_mail'):
    ADMINS = (
        ("Xelpaste admins", config.get('dev.admin_mail')),
    )



# URLs
# ====

ALLOWED_HOSTS = config.getlist('django.allowed_hosts')
DPASTE_BASE_URL = config.get('xelpaste.url')
DPASTE_DOMAIN = config.get('xelpaste.domain')


# Loadable components
# ===================

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'django.contrib.sessions',

    'mptt',
    'south',
    'dpaste',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'dpaste.context_processors.dpaste_settings',
)

ROOT_URLCONF = 'dpaste.urls'


# Database
# ========

DATABASES = {
    'default': {
        'ENGINE': config.get('db.engine', 'django.db.backends.sqlite3'),
        'NAME': config.get('db.name', os.path.join(CHECKOUT_DIR, 'db.sqlite3')),
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

STATIC_URL = config.get('django.static_url', '/static/')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


# Snippets
# ========


def parse_size(size):
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


MEDIA_ROOT = config.get('uploads.dir', os.path.join(CHECKOUT_DIR, 'media'))
DPASTE_UPLOAD_TO = 'snippets'
SENDFILE_BACKEND = 'sendfile.backends.%s' % config.get('uploads.serve', 'simple')
SENDFILE_ROOT = os.path.join(MEDIA_ROOT, DPASTE_UPLOAD_TO)
SENDFILE_URL = config.get('uploads.internal_url', '/uploads/')

DPASTE_MAX_CONTENT_LENGTH = parse_size(config.get('snippets.max_content', '1MB'))
DPASTE_MAX_FILE_LENGTH = parse_size(config.get('snippets.max_file', '10MB'))
SLUG_LENGTH = config.getint('snippets.slug_length', 4)

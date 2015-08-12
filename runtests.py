#!/usr/bin/env python
import sys
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'dev.db',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.sessions',
            'django.contrib.staticfiles',
            'mptt',
            'xelpaste',
        ],
        STATIC_ROOT='/tmp/xelpaste_test_static/',
        STATIC_URL='/static/',
        ROOT_URLCONF='xelpaste.urls',
    )

def runtests(*test_args):
    from django.test.simple import DjangoTestSuiteRunner
    test_runner = DjangoTestSuiteRunner(verbosity=1)
    failures = test_runner.run_tests(['xelpaste', ])
    if failures:
        sys.exit(failures)

if __name__ == '__main__':
    runtests(*sys.argv[1:])

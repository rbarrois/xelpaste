#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'xelpaste.settings'
    os.environ.setdefault('XELPASTE_APP_MODE', 'dev')

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re

from setuptools import setup, find_packages

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return ''


PACKAGE = 'xelpaste'
setup(
    # Contents
    name=PACKAGE,
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/xelpastectl'],

    # Metadata
    version=get_version(PACKAGE),
    description="Standalone, django-based pastebin with image support.",
    long_description=''.join(codecs.open('README.rst', 'r', 'utf-8').readlines()),
    author='Martin Mahner',
    maintainer="Raphaël Barrois",
    maintainer_email='raphael.barrois+%s@polytechnique.org' % PACKAGE,
    url='https://github.com/rbarrois/%s/' % PACKAGE,
    keywords=['xelpaste', 'dpaste', 'pastebin'],
    license='MIT',

    # Dependencies
    install_requires=[
        'django>=1.7',
        'django-mptt>=0.6.0',
        'pygments>=1.6',
        'requests>=2.0.0',
    ],
    tests_require=[
    ],

    # Misc
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],
)

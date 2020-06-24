#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import glob
import os
import re
import subprocess
import sys

from setuptools import setup, find_packages
from setuptools.command import build_py

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


def find_package_data(patterns):
    package_data = {}
    for pattern in patterns:
        package, subpattern = pattern.split('/', 1)
        matched = glob.glob(pattern, recursive=True)
        package_data.setdefault(package, []).extend([
            # We need the paths relative to their package.
            path.split('/', 1)[1] for path in matched
        ])
    return package_data


class BuildWithMakefile(build_py.build_py):
    """Custom 'build' command that runs 'make build' first."""
    def run(self):
        # Ensure the checked-out folder comes first.
        # We install the project as `pip install -e .`, but zest
        # will assemble the bdist_wheel from a temporary location;
        # this makes sure that the module picked as DJANGO_SETTINGS_MODULE
        # is the file from the temporary location, and all files get written
        # within that temporary location, and not the original git checkout.

        env = dict(os.environ)
        env['PYTHONPATH'] = ':'.join(
            [
                os.path.dirname(__file__)
            ] + env.get('PYTHONPATH', '').split(':')
        )
        subprocess.check_call(['make', 'build'], env=env)

        # Recompute package data
        self.package_data = find_package_data(PACKAGE_DATA_PATTERNS)

        # Override the cached set of data_files.
        self.data_files = self._get_data_files()
        return super().run()


PACKAGE = 'xelpaste'
PACKAGE_DATA_PATTERNS = [
    'xelpaste/assets/**/*',
    'xelpaste/static/**/*',
    'xelpaste/locale/**/*.mo',
]




setup(
    # Contents
    name=PACKAGE,
    packages=find_packages(exclude=['dev', 'tests*']),

    # Ref: https://stackoverflow.com/questions/24347450/how-do-you-add-additional-files-to-a-wheel/49501350#49501350
    # Yep, the Python docs are false here.
    package_data=find_package_data(PACKAGE_DATA_PATTERNS),
    include_package_data=True,
    scripts=['bin/xelpastectl'],
    cmdclass={'build_py': BuildWithMakefile},
    zip_safe=False,

    # Metadata
    version=get_version(PACKAGE),
    description="Standalone, django-based pastebin with image support.",
    long_description=''.join(codecs.open('README.rst', 'r', 'utf-8').readlines()),
    author='Martin Mahner',
    maintainer="Raphaël Barrois",
    maintainer_email='raphael.barrois+%s@polytechnique.org' % PACKAGE,
    author_email='raphael.barrois+%s@polytechnique.org' % PACKAGE,
    url='https://github.com/rbarrois/%s/' % PACKAGE,
    keywords=['xelpaste', 'dpaste', 'pastebin'],
    license='MIT',

    # Dependencies
    install_requires=[
        'Django>=2.0,<3.0',
        'django-mptt>=0.9.1',
        'pygments>=2.2.0',
        'django-appconf>=1.0.1',
        'django-sendfile2',
        'getconf>=1.3.0,<2',
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

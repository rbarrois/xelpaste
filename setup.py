#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
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


class BuildWithMakefile(build_py.build_py):
    """Custom 'build' command that runs 'make build' first."""
    def run(self):
        subprocess.check_call(['make', 'update-js'])
        subprocess.check_call(['make', 'build'])
        if sys.version_info[0] < 3:
            # Under Python 2.x, build_py is an old-style class.
            return build_py.build_py.run(self)
        return super().run()


PACKAGE = 'xelpaste'


setup(
    # Contents
    name=PACKAGE,
    packages=find_packages(exclude=['dev', 'tests*']),
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
        'django-mptt>=0.9.1,<0.10',
        'pygments>=2.2.0,<2.3',
        'django-appconf>=1.0.1,<1.1',
        'django-sendfile>=0.3.9,<0.4',
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

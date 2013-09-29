#!/usr/bin/env python
from setuptools import setup

from mise_a_feu.scripts.update_stack import get_version

with open('README.md') as file:
    long_description = file.read()

setup(
    name = "mise-a-feu",
    packages = [ 'mise_a_feu' ],
    version = get_version(),
    url = '',
    author = '',
    author_email = '',
    description = "Module to handle deployment of a stack of packages.",
    long_description=long_description,
    include_package_data = True,
    entry_points = {
        "console_scripts" : [ "mise-a-feu = mise_a_feu.fabfile:main"]
    },
    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Environment :: Web',
                   'License :: OSI Approved :: GNU Affero General Public License v3',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
    install_requires = open('requirements.pip').readlines(),
)

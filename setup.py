#!/usr/bin/env python3

from setuptools import setup, find_packages

dépendances=['cbor', 'docker']

entrées = {
    'console_scripts': [
        'docker-exerciseur = main:main'
        ]
    }

setup(
    name="docker-exerciseur",
    version="0.1",
    packages=find_packages('src'),
    author='Florent Becker <florent.becker@univ-orleans.fr>',
    install_requires=dépendances,
    entry_points = entrées,
    package_dir={'': 'src'},
)      

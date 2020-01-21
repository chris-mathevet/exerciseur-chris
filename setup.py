#!/usr/bin/env python3

from setuptools import setup, find_packages

dépendances=['cbor >= 1.0.0', 'docker >= 4.1.0']

entrées = {
    'console_scripts': [
        'docker-exerciseur = docker_exerciseur.main:main'
        ]
    }

setup(
    name="docker-exerciseur",
    version="0.1",
    packages=find_packages(),
    author='Florent Becker <florent.becker@univ-orleans.fr>',
    install_requires=dépendances,
    entry_points = entrées,
#    package_dir={'': 'src'},
)      

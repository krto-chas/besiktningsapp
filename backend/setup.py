#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============================================================================
BESIKTNINGSAPP BACKEND - SETUP
=============================================================================
Setup configuration for the backend package.
"""

from setuptools import setup, find_packages
import os


def read_requirements(filename):
    """Read requirements from file."""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r', encoding='utf-8') as f:
        return [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#') and not line.startswith('-r')
        ]


def read_file(filename):
    """Read file content."""
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


# Package metadata
NAME = 'besiktningsapp-backend'
DESCRIPTION = 'Backend API for Besiktningsapp - Offline-first mobile inspection application'
VERSION = '1.0.0'
AUTHOR = 'Besiktningsapp Team'
AUTHOR_EMAIL = 'dev@besiktningsapp.se'
URL = 'https://github.com/yourusername/besiktningsapp'
LICENSE = 'Proprietary'

# Read long description from README
LONG_DESCRIPTION = read_file('README.md')

# Read requirements
INSTALL_REQUIRES = read_requirements('requirements.txt')
DEV_REQUIRES = read_requirements('requirements-dev.txt')

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    
    # Package discovery
    packages=find_packages(exclude=['tests', 'tests.*', 'docs']),
    include_package_data=True,
    
    # Python version
    python_requires='>=3.11',
    
    # Dependencies
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
    },
    
    # Entry points
    entry_points={
        'console_scripts': [
            'besiktningsapp-backend=app.main:cli',
        ],
    },
    
    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    
    # Keywords
    keywords='flask api rest backend inspection offline-first sync',
    
    # Project URLs
    project_urls={
        'Documentation': 'https://docs.besiktningsapp.se',
        'Source': 'https://github.com/yourusername/besiktningsapp',
        'Tracker': 'https://github.com/yourusername/besiktningsapp/issues',
    },
    
    # Zip safe
    zip_safe=False,
)

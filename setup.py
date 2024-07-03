#!/usr/bin/env python

from distutils.core import setup
from distutils.extension import Extension
#from Cython.Distutils import build_ext

setup(
  name = 'eggd800',
  version='0.0.2',
  packages = ['eggd800'],
  scripts = [
    'scripts/eggzero',
    'scripts/eggd800'
  ],
  classifiers = [
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering'
  ]
)

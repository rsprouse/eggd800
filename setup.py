#!/usr/bin/env python

from distutils.core import setup
from distutils.extension import Extension
#from Cython.Distutils import build_ext

setup(
  name = 'eggd800',
  packages = ['eggd800'],
  scripts = [
    'scripts/eggzero'
  ],
  classifiers = [
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering'
  ]
)

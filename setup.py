#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys

VERSION = "0.6"

copy_args = sys.argv[1:]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='modelcif',
      version=VERSION,
      script_args=copy_args,
      description='Package for handling ModelCIF mmCIF and BinaryCIF files',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Ben Webb',
      author_email='ben@salilab.org',
      url='https://github.com/ihmwg/python-modelcif',
      packages=['modelcif'],
      install_requires=['ihm>=0.34'],
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering",
      ])

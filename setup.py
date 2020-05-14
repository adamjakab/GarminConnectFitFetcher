#!/usr/bin/env python

from setuptools import find_packages
from distutils.core import setup

setup(name="Garmin Connect Fit Fetcher",
      version="1.0.0",
      description="Garmin Connect Fit Fetcher.",
      long_description=open('README.md').read(),
      author="Adam Jakab",
      author_email="adam@jakab.pro",

      license=open('LICENSE').read(),
      url="https://github.com/adamjakab/GarminConnectFitFetcher",

      packages=["gcff"],
      install_requires=[
          "garminexport"
      ],
      classifiers=[
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop'
          'Natural Language :: English',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3.5+',
      ]
      )

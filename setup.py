#!/usr/bin/env python

from distutils.core import setup

setup(name='mustache_to_handlebars',
      version='0.95',
      description='converts mustache to handlebars templates',
      author='Justin Black',
      url='https://github.com/spacether/mustache_to_handlebars',
      packages=['mustache_to_handlebars'],
      entry_points={
            'console_scripts': [
                  'mustache_to_handlebars=mustache_to_handlebars.main:mustache_to_handlebars'
            ],
      },
      extras_require={
            'dev': [
                  'pytest',
                  'black',
            ]
      },
      python_requires='>=3.7',
)
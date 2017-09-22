#!/usr/bin/env python

from io import open
import os
import subprocess
import sys

from setuptools import setup, Command, find_packages

import pkgdist


test_requirements = ['pytest']
if sys.hexversion < 0x03030000:
    test_requirements.append('mock')

setup(
    name=pkgdist.MODULE,
    version=pkgdist.version(),
    description='a python library and cli tool that simplify chroot handling',
    long_description=pkgdist.readme(),
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'':'src'},
    scripts=os.listdir('bin'),
    install_requires=pkgdist.install_requires(),
    tests_require=test_requirements,
    platforms='Posix',
    cmdclass={
        'build_py': pkgdist.build_py2to3,
        'build_scripts': pkgdist.build_scripts,
        'build_man': pkgdist.build_man,
        'build_docs': pkgdist.build_docs,
        'install_man': pkgdist.install_man,
        'install_docs': pkgdist.install_docs,
        'sdist': pkgdist.sdist,
        'test': pkgdist.pytest,
        'lint': pkgdist.pylint,
    },
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
)

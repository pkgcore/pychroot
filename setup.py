#!/usr/bin/env python

from setuptools import setup

import pkgdist
pkgdist_setup, pkgdist_cmds = pkgdist.setup()

setup(
    description='a python library and cli tool that simplify chroot handling',
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    platforms='Posix',
    cmdclass=dict(
        build_py=pkgdist.build_py2to3,
        test=pkgdist.pytest,
        lint=pkgdist.pylint,
        **pkgdist_cmds
    ),
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
    **pkgdist_setup
)

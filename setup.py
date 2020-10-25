#!/usr/bin/env python3

from setuptools import setup

from snakeoil.dist import distutils_extensions as pkgdist
pkgdist_setup, pkgdist_cmds = pkgdist.setup()


setup(**dict(pkgdist_setup,
    description='a python library and cli tool that simplify chroot handling',
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    platforms='Posix',
    tests_require=pkgdist.test_requires(),
    cmdclass=dict(
        pkgdist_cmds,
        test=pkgdist.pytest,
        lint=pkgdist.pylint,
        ),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        ],
    )
)

#!/usr/bin/env python

from io import open
import os
import subprocess
import sys

from setuptools import setup, Command, find_packages

import pkgdist


class PyTest(pkgdist.PyTest):

    default_test_dir = os.path.join(pkgdist.TOPDIR, 'test')


class PyLint(Command):
    user_options = [('errorsonly', 'E', 'Check only errors with pylint'),
                    ('format=', 'f', 'Change the output format')]

    def initialize_options(self):
        self.errorsonly = 0
        self.format = 'colorized'

    def finalize_options(self):
        pass

    def run(self):
        rcfile = os.path.abspath('.pylintrc')
        standaloneModules = [m for m in []]
        cli_options = ['-E'] if self.errorsonly else []
        cli_options.append('--output-format={0}'.format(self.format))
        errno = subprocess.call([sys.executable, '-m', 'pylint', '--rcfile={}'.format(rcfile), '--output-format=colorized'] +
                                cli_options + ['pychroot'] + standaloneModules)
        raise SystemExit(errno)

test_requirements = ['pytest']
if sys.hexversion < 0x03030000:
    test_requirements.append('mock')

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()
with open('NEWS.rst', 'r', encoding='utf-8') as f:
    news = f.read()

setup(
    name='pychroot',
    version=pkgdist.version(),
    description='a python library and cli tool that simplify chroot handling',
    long_description=readme + '\n\n' + news,
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    packages=find_packages(),
    scripts=os.listdir('bin'),
    install_requires=['snakeoil>=0.7.1'],
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
        'test': PyTest,
        'lint': PyLint,
    },
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ),
)

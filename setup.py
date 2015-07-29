#!/usr/bin/env python

import os
import subprocess
import sys

from setuptools import setup, Command

from chroot import __version__


class PyTest(Command):
    user_options = [('match=', 'k', 'Run only tests that match the provided expressions')]

    def initialize_options(self):
        self.match = None

    def finalize_options(self):
        pass

    def run(self):
        cli_options = ['-k', self.match] if self.match else []
        errno = subprocess.call([sys.executable, '-m', 'pytest'] + cli_options)
        raise SystemExit(errno)


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
                                cli_options + ['chroot'] + standaloneModules)
        raise SystemExit(errno)

test_requirements = ['pytest']
if sys.hexversion < 0x03030000:
    test_requirements.append('mock')

with open('README.rst', 'r') as f:
    readme = f.read()

setup(
    name='pychroot',
    version=__version__,
    description='a python library that simplifies chroot handling',
    long_description=readme,
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    packages=['chroot'],
    entry_points={'console_scripts': ['pychroot = chroot.cli:main']},
    install_requires=['snakeoil>=0.6.5'],
    tests_require=test_requirements,
    use_2to3=True,
    platforms='Posix',
    cmdclass={'test': PyTest, 'lint': PyLint},
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ),
)

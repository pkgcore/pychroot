#!/usr/bin/env python

from io import open
import os
import re
import subprocess
import sys

from setuptools import setup, Command, find_packages

from snakeoil.dist import distutils_extensions as pkgdist


class mysdist(pkgdist.sdist):

    """sdist command specifying the right files."""

    user_options = pkgdist.sdist.user_options + [
        ('build-docs', None, 'build docs'),
    ]

    boolean_options = pkgdist.sdist.boolean_options + ['build-docs']

    def initialize_options(self):
        pkgdist.sdist.initialize_options(self)
        self.build_docs = False

    def make_release_tree(self, base_dir, files):
        """Create and populate the directory tree that is put in source tars.

        This copies or hardlinks "normal" source files that should go
        into the release and adds generated files that should not
        exist in a working tree.
        """
        import shutil
        cwd = os.getcwd()

        if self.build_docs:
            # need to make sure we're using a built version of pkgcore for the
            # current python version since doc/conf.py imports pkgcore modules
            build_py = self.get_finalized_command('build_py')
            build_py.run()
            if subprocess.call([sys.executable, 'setup.py', 'build_man'], cwd=cwd):
                raise DistutilsExecError("build_man failed")
            shutil.copytree(os.path.join(cwd, "build/sphinx/man"),
                            os.path.join(base_dir, "man"))
        pkgdist.sdist.make_release_tree(self, base_dir, files)


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
                                cli_options + ['pychroot'] + standaloneModules)
        raise SystemExit(errno)

test_requirements = ['pytest']
if sys.hexversion < 0x03030000:
    test_requirements.append('mock')

version = ''
with open('pychroot/__init__.py', 'r', encoding='utf-8') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version')

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()
with open('NEWS.rst', 'r', encoding='utf-8') as f:
    news = f.read()

setup(
    name='pychroot',
    version=version,
    description='a python library and cli tool that simplify chroot handling',
    long_description=readme + '\n\n' + news,
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    packages=find_packages(),
    entry_points={'console_scripts': ['pychroot = pychroot.cli:main']},
    install_requires=['snakeoil>=0.6.5'],
    setup_requires=['snakeoil>=0.6.5'],
    tests_require=test_requirements,
    platforms='Posix',
    cmdclass={
        'build_py': pkgdist.build_py,
        'sdist': mysdist,
        'test': PyTest,
        'lint': PyLint,
    },
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ),
)

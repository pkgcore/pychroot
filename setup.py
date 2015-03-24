import os
import sys
import subprocess

from setuptools import setup, Command, Extension

import chroot


class RunCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class PyTest(RunCommand):
    user_options = [('match=', 'k', 'Run only tests that match the provided expressions')]

    def initialize_options(self):
        self.match = None

    def run(self):
        cli_options = ['-k', self.match] if self.match else []
        os.environ['EPYTHON'] = 'python{}.{}'.format(sys.version_info.major, sys.version_info.minor)
        errno = subprocess.call(['py.test'] + cli_options)
        raise SystemExit(errno)


class PyLint(RunCommand):
    user_options = [('errorsonly', 'E', 'Check only errors with pylint'),
                    ('format=', 'f', 'Change the output format')]

    def initialize_options(self):
        self.errorsonly = 0
        self.format = 'colorized'

    def run(self):
        rcfile = os.path.abspath('.pylintrc')
        os.environ['EPYTHON'] = 'python{}.{}'.format(sys.version_info.major, sys.version_info.minor)
        standaloneModules = [m for m in []]
        cli_options = ['-E'] if self.errorsonly else []
        cli_options.append('--output-format={0}'.format(self.format))
        errno = subprocess.call(['pylint', '--rcfile={}'.format(rcfile), '--output-format=colorized'] +
                                cli_options + ['chroot'] + standaloneModules)
        raise SystemExit(errno)


with open('README.rst', 'r') as f:
    readme = f.read()

setup(
    name='chroot',
    version=chroot.__version__,
    description='Python module to make working with chroots much easier',
    long_description=readme,
    author='Tim Harder',
    author_email='radhermit@gmail.com',
    url='https://github.com/pkgcore/pychroot',
    license='BSD',
    packages=['chroot'],
    platforms='Posix',
    use_2to3=True,
    cmdclass={'test': PyTest, 'lint': PyLint},
)

from __future__ import unicode_literals

import errno
import os
import shlex
import tempfile
try:
    from unittest import mock
except ImportError:
    import mock

import pytest
from pytest import raises

from pychroot import cli


def test_arg_parsing():
    # one argument required
    with raises(TypeError):
        cli.parse_args()

    # unknown args
    with raises(SystemExit):
        opts = cli.parse_args('--foo --bar dir'.split())

    # single newroot arg with $SHELL from env
    with mock.patch('os.getenv', return_value='shell'):
        opts = cli.parse_args(['dir'])
        assert opts.path == 'dir'
        assert opts.command == ['shell', '-i']
        assert opts.mountpoints is None

    # default shell when $SHELL isn't defined in the env
    with mock.patch.dict('os.environ', {}, clear=True):
        opts = cli.parse_args(['dir'])
        assert opts.command == ['/bin/sh', '-i']

    # complex args
    opts = cli.parse_args(shlex.split('-R /home -B /tmp --ro /var dir cmd arg "arg1 arg2"'))
    assert opts.path == 'dir'
    assert opts.command == ['cmd', 'arg', 'arg1 arg2']
    assert opts.path == 'dir'
    assert opts.mountpoints == {
        '/home': {'recursive': True, 'readonly': False},
        '/tmp': {'recursive': False, 'readonly': False},
        '/var': {'recursive': False, 'readonly': True},
    }


def test_cli():
    # no root perms
    with raises(SystemExit):
        cli.main(['nonexistent-dir'])

    with mock.patch('os.geteuid', return_value=0), \
            mock.patch('os.fork') as fork, \
            mock.patch('os.chroot') as chroot, \
            mock.patch('os._exit') as exit, \
            mock.patch('os.waitpid') as waitpid, \
            mock.patch('pychroot.utils.mount') as mount, \
            mock.patch('os.execvp') as execvp, \
            mock.patch('pychroot.base.simple_unshare'):

        # no args
        with raises(SystemExit):
            cli.main([])

        # nonexistent newroot dir
        with raises(SystemExit):
            cli.main(['nonexistent-dir'])

    with mock.patch('pychroot.cli.Chroot'), \
            mock.patch('os.execvp') as execvp:

        chroot = tempfile.mkdtemp()

        # exec arg testing
        cli.main([chroot])
        shell = os.getenv('SHELL', '/bin/sh')
        execvp.assert_called_once_with(shell, [shell, '-i'])
        execvp.reset_mock()

        cli.main([chroot, 'ls -R /'])
        execvp.assert_called_once_with('ls -R /', ['ls -R /'])
        execvp.reset_mock()

        e = EnvironmentError("command doesn't exist")
        e.errno = errno.ENOENT
        execvp.side_effect = e
        with raises(SystemExit):
            cli.main([chroot])
        execvp.reset_mock()

        e = EnvironmentError('fake exception')
        e.errno = errno.EIO
        execvp.side_effect = e
        with raises(EnvironmentError):
            cli.main([chroot])
        execvp.reset_mock()

        os.rmdir(chroot)

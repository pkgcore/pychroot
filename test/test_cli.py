from __future__ import absolute_import, unicode_literals

import errno
from functools import partial
import os
import shlex
import tempfile
try:
    from unittest import mock
except ImportError:
    import mock

from pytest import raises

from pychroot import scripts
from pychroot.base import Chroot
from pychroot.scripts.pychroot import parse_args


def test_arg_parsing():
    # one argument required
    with raises(TypeError):
        parse_args()

    # unknown args
    with raises(SystemExit):
        opts = parse_args('--foo --bar fakedir'.split())

    # no mounts
    orig_default_mounts = Chroot.default_mounts.copy()
    opts = parse_args('--no-mounts fakedir'.split())
    assert Chroot.default_mounts == {}
    Chroot.default_mounts = orig_default_mounts
    assert Chroot.default_mounts != {}

    # single newroot arg with $SHELL from env
    with mock.patch('os.getenv', return_value='shell'):
        opts = parse_args(['dir'])
        assert opts.path == 'dir'
        assert opts.command == ['shell', '-i']
        assert opts.mountpoints is None

    # default shell when $SHELL isn't defined in the env
    with mock.patch.dict('os.environ', {}, clear=True):
        opts = parse_args(['dir'])
        assert opts.command == ['/bin/sh', '-i']

    # complex args
    opts = parse_args(shlex.split('-R /home -B /tmp --ro /var dir cmd arg "arg1 arg2"'))
    assert opts.path == 'dir'
    assert opts.command == ['cmd', 'arg', 'arg1 arg2']
    assert opts.path == 'dir'
    assert opts.mountpoints == {
        '/home': {'recursive': True, 'readonly': False},
        '/tmp': {'recursive': False, 'readonly': False},
        '/var': {'recursive': False, 'readonly': True},
    }


def test_cli():
    cli = partial(scripts.main, 'pychroot')

    # no root perms
    with raises(SystemExit):
        cli(['nonexistent-dir'])

    with mock.patch('os.geteuid', return_value=0), \
            mock.patch('os.fork'), \
            mock.patch('os.chroot') as chroot, \
            mock.patch('os._exit'), \
            mock.patch('os.waitpid'), \
            mock.patch('pychroot.utils.mount'), \
            mock.patch('os.execvp') as execvp, \
            mock.patch('pychroot.scripts.import_module') as import_module, \
            mock.patch('pychroot.base.simple_unshare'):

        # import failure
        import_module.side_effect = ImportError("module doesn't exist")
        with raises(SystemExit):
            cli([])
        with raises(ImportError):
            cli(['--debug'])
        import_module.reset_mock()

        # no args
        with raises(SystemExit):
            cli([])

        # nonexistent newroot dir
        with raises(SystemExit):
            cli(['nonexistent-dir'])

    with mock.patch('pychroot.scripts.pychroot.Chroot'), \
            mock.patch('os.execvp') as execvp:

        chroot = tempfile.mkdtemp()

        # exec arg testing
        cli([chroot])
        shell = os.getenv('SHELL', '/bin/sh')
        execvp.assert_called_once_with(shell, [shell, '-i'])
        execvp.reset_mock()

        cli([chroot, 'ls -R /'])
        execvp.assert_called_once_with('ls -R /', ['ls -R /'])
        execvp.reset_mock()

        e = EnvironmentError("command doesn't exist")
        e.errno = errno.ENOENT
        execvp.side_effect = e
        with raises(SystemExit):
            cli([chroot])
        execvp.reset_mock()

        e = EnvironmentError('fake exception')
        e.errno = errno.EIO
        execvp.side_effect = e
        with raises(EnvironmentError):
            cli([chroot])
        execvp.reset_mock()

        os.rmdir(chroot)

import shlex
from unittest.mock import patch

from snakeoil.cli.tool import Tool

from pychroot.scripts.pychroot import argparser
from pychroot.base import Chroot


def test_arg_parsing():
    """Various argparse checks."""
    # no mounts
    orig_default_mounts = Chroot.default_mounts.copy()
    opts = argparser.parse_args('--no-mounts fakedir'.split())
    assert Chroot.default_mounts == {}
    Chroot.default_mounts = orig_default_mounts
    assert Chroot.default_mounts != {}

    # single newroot arg with $SHELL from env
    with patch('os.getenv', return_value='shell'):
        opts = argparser.parse_args(['dir'])
        assert opts.path == 'dir'
        assert opts.command == ['shell', '-i']
        assert opts.mountpoints is None

    # default shell when $SHELL isn't defined in the env
    with patch.dict('os.environ', {}, clear=True):
        opts = argparser.parse_args(['dir'])
        assert opts.command == ['/bin/sh', '-i']

    # complex args
    opts = argparser.parse_args(shlex.split(
        '-R /home -B /tmp --ro /var dir cmd arg "arg1 arg2"'))
    assert opts.path == 'dir'
    assert opts.command == ['cmd', 'arg', 'arg1 arg2']
    assert opts.path == 'dir'
    assert opts.mountpoints == {
        '/home': {'recursive': True, 'readonly': False},
        '/tmp': {'recursive': False, 'readonly': False},
        '/var': {'recursive': False, 'readonly': True},
    }


def test_cli(capfd, tmp_path):
    """Various command line interaction checks."""
    pychroot = Tool(argparser)

    # no args
    ret = pychroot([])
    assert ret == 2
    out, err = capfd.readouterr()
    assert err.startswith("pychroot: error: ")

    # nonexistent directory
    ret = pychroot(['nonexistent'])
    assert ret == 1
    out, err = capfd.readouterr()
    assert err == (
        "pychroot: error: cannot change root directory "
        "to 'nonexistent': Not a directory\n")

    with patch('pychroot.scripts.pychroot.Chroot'), \
            patch('os.getenv', return_value='/bin/sh'), \
            patch('subprocess.run') as run:
        chroot = str(tmp_path)

        # exec arg testing
        pychroot([chroot])
        shell = '/bin/sh'
        run.assert_called_once_with([shell, '-i'])
        run.reset_mock()

        pychroot([chroot, 'ls -R /'])
        run.assert_called_once_with(['ls -R /'])
        run.reset_mock()

        e = FileNotFoundError("command doesn't exist")
        run.side_effect = e
        pychroot([chroot, 'nonexistent'])
        out, err = capfd.readouterr()
        assert err == f"pychroot: error: failed to run command 'nonexistent': {e}\n"
        run.reset_mock()

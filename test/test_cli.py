import shlex
try:
    from unittest import mock
except ImportError:
    import mock

from pytest import raises

from chroot import cli


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
        assert 'mountpoints' not in opts

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
    with raises(SystemExit) as e:
        cli.main(['nonexistent-dir'])
        assert 'permissions' in str(e.value)

    # pretend we're root
    with mock.patch('os.geteuid', return_value=0):
        # no args
        with raises(SystemExit):
            cli.main([])

        # nonexistent newroot dir
        with raises(SystemExit) as e:
            cli.main(['nonexistent-dir'])
            assert 'nonexistent path' in str(e.value)

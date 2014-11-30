import errno
import logging
import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock
from mock import mock_open, patch
from pytest import raises

from chroot.utils import dictbool, getlogger, bind, MountError


def test_dictbool():
    assert dictbool({'a': True}, 'a')
    assert not dictbool({'a': True}, 'b')
    assert not dictbool({'a': False}, 'a')


def test_getlogger():
    log = getlogger(logging.Logger, __name__)
    assert type(log) == logging.Logger


def test_bind():
    with raises(MountError):
        bind('/nonexistent/src/path', '/randomdir')
    with raises(MountError):
        bind('tmpfs', '/nonexistent/dest/path')
    with patch('chroot.utils.call', return_value=1):
        with raises(MountError):
                bind('proc', '/root')

    # create
    with patch('chroot.utils.call') as call, \
            patch('chroot.utils.os.path.isdir') as isdir, \
            patch('chroot.utils.os.makedirs') as makedirs, \
            patch('chroot.utils.open', mock_open(), create=True) as mopen, \
            patch('chroot.utils.os.path.exists', return_value=True):

        call.return_value = 0

        isdir.return_value = True
        bind('/fake/src', '/fake/dest', create=True)
        makedirs.assert_called_once_with('/fake/dest')
        assert not mopen.called

        makedirs.reset_mock()

        e = OSError('fake exception')
        e.errno = errno.EIO
        makedirs.side_effect = e
        with raises(OSError):
            bind('/fake/src', '/fake/dest', create=True)

        makedirs.reset_mock()
        makedirs.side_effect = None

        isdir.return_value = False
        bind('/fake/src', '/fake/dest', create=True)
        makedirs.assert_called_once_with('/fake')
        mopen.assert_called_once_with('/fake/dest', 'w')

        call.side_effect = [0, 1]
        with raises(MountError):
            bind('/', '/root', readonly=True)

import errno
import logging

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
        bind('/nonexistent/src/path', '/randomdir', '/chroot/path')
    with raises(MountError):
        bind('tmpfs', '/nonexistent/dest/path', '/chroot/path')
    with patch('chroot.utils.mount', side_effect=OSError):
        with raises(MountError):
            bind('proc', '/root', '/chroot/path')

    # create
    with patch('chroot.utils.mount') as mount, \
            patch('os.path.isdir') as isdir, \
            patch('os.makedirs') as makedirs, \
            patch('chroot.utils.open', mock_open(), create=True) as mopen, \
            patch('os.path.exists', return_value=True):

        isdir.return_value = True
        bind('/fake/src', '/fake/dest', '/chroot/path', create=True)
        makedirs.assert_called_once_with('/fake/dest')
        assert not mopen.called

        makedirs.reset_mock()

        e = OSError('fake exception')
        e.errno = errno.EIO
        makedirs.side_effect = e
        with raises(OSError):
            bind('/fake/src', '/fake/dest', '/chroot/path', create=True)

        makedirs.reset_mock()
        makedirs.side_effect = None

        isdir.return_value = False
        bind('/fake/src', '/fake/dest', '/chroot/path', create=True)
        makedirs.assert_called_once_with('/fake')
        mopen.assert_called_once_with('/fake/dest', 'w')

        #with raises(MountError):
            #bind('/', '/root', readonly=True)

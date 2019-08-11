import errno
import logging
import os
from unittest import mock

from pytest import raises
from snakeoil.osutils.mount import MS_BIND, MS_REC, MS_REMOUNT, MS_RDONLY

from pychroot.utils import dictbool, getlogger, bind
from pychroot.exceptions import ChrootMountError


def test_dictbool():
    assert dictbool({'a': True}, 'a')
    assert not dictbool({'a': True}, 'b')
    assert not dictbool({'a': False}, 'a')


def test_getlogger():
    log = getlogger(logging.Logger, __name__)
    assert type(log) == logging.Logger


def test_bind(tmp_path):
    with raises(ChrootMountError):
        bind('/nonexistent/src/path', '/randomdir', '/chroot/path')
    with raises(ChrootMountError):
        bind('tmpfs', '/nonexistent/dest/path', '/chroot/path')
    with mock.patch('pychroot.utils.mount', side_effect=OSError):
        with raises(ChrootMountError):
            bind('proc', '/root', '/chroot/path')

    # create
    with mock.patch('pychroot.utils.mount') as mount, \
            mock.patch('os.path.isdir') as isdir, \
            mock.patch('os.makedirs') as makedirs:
        src = tmp_path / 'pychroot-src'
        src.mkdir()
        src = str(src)
        chroot = tmp_path / 'pychroot-chroot'
        chroot.mkdir()
        chroot = str(chroot)
        dest = os.path.join(chroot, 'dest')
        destfile = os.path.join(chroot, 'destfile')
        os.mkdir(dest)

        isdir.return_value = True
        bind(src, dest, chroot, create=True)
        makedirs.assert_called_once_with(dest)

        makedirs.reset_mock()

        ## mounting on top of a symlink
        # symlink points to an existing path
        os.symlink('/dest', os.path.join(chroot, 'existing'))
        bind(src, os.path.join(chroot, 'existing'), chroot, create=False)
        assert not makedirs.called

        makedirs.reset_mock()

        # broken symlink
        # usually this would raise ChrootMountError but we're catching the makedirs call
        with raises(ChrootMountError):
            os.symlink('/nonexistent', os.path.join(chroot, 'broken'))
            bind(src, os.path.join(chroot, 'broken'), chroot, create=False)
            makedirs.assert_called_once_with(os.path.join(chroot, 'nonexistent'))

        makedirs.reset_mock()

        e = OSError('fake exception')
        e.errno = errno.EIO
        makedirs.side_effect = e
        with raises(OSError):
            bind(src, dest, chroot, create=True)

        makedirs.reset_mock()
        makedirs.side_effect = None

        # bind an individual file
        isdir.return_value = False
        bind(src, destfile, chroot, create=True)
        makedirs.assert_called_once_with(chroot)

        mount.reset_mock()

        # recursive mount
        isdir.return_value = True
        bind(src, dest, chroot, create=True, recursive=True)
        mount.assert_called_once_with(
            source=src, target=dest, fstype=None,
            flags=(MS_BIND | MS_REC), data='')

        mount.reset_mock()

        # readonly mount
        isdir.return_value = True
        bind(src, dest, chroot, create=True, readonly=True)
        call1 = mock.call(
            source=src, target=dest, fstype=None, flags=(MS_BIND), data='')
        call2 = mock.call(
            source=src, target=dest, fstype=None,
            flags=(MS_BIND | MS_REMOUNT | MS_RDONLY), data='')
        mount.assert_has_calls([call1, call2])

        #with raises(ChrootMountError):
            #bind('/', '/root', readonly=True)

import errno
import logging
import os
import shutil
from tempfile import mkdtemp

try:
    from unittest import mock
except ImportError:
    import  mock
from pytest import raises
from snakeoil.osutils import MS_BIND, MS_REC, MS_REMOUNT, MS_RDONLY

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
    with mock.patch('chroot.utils.mount', side_effect=OSError):
        with raises(MountError):
            bind('proc', '/root', '/chroot/path')

    # create
    with mock.patch('chroot.utils.mount') as mount, \
            mock.patch('os.path.isdir') as isdir, \
            mock.patch('os.makedirs') as makedirs, \
            mock.patch('chroot.utils.open', mock.mock_open(), create=True) as mock_open:

        try:
            # tempfile.TemporaryDirectory is only availabile in >=3.2
            src = mkdtemp(prefix='pychroot-src')
            chroot = mkdtemp(prefix='pychroot-chroot')
            dest = os.path.join(chroot, 'dest')
            os.mkdir(dest)

            isdir.return_value = True
            bind(src, dest, chroot, create=True)
            makedirs.assert_called_once_with(dest)
            assert not mock_open.called

            makedirs.reset_mock()

            ## mounting on top of a symlink
            # symlink points to an existing path
            os.symlink('/dest', os.path.join(chroot, 'existing'))
            bind(src, os.path.join(chroot, 'existing'), chroot, create=False)
            assert not makedirs.called

            makedirs.reset_mock()

            # broken symlink
            # usually this would raise MountError but we're catching the makedirs call
            with raises(MountError):
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

            isdir.return_value = False
            bind(src, dest, chroot, create=True)
            makedirs.assert_called_once_with(chroot)
            mock_open.assert_called_once_with(dest, 'w')

            mount.reset_mock()

            # recursive mount
            isdir.return_value = True
            bind(src, dest, chroot, create=True, recursive=True)
            mount.assert_called_once_with(source=src, target=dest, fstype='none', flags=(MS_BIND | MS_REC), data='')

            mount.reset_mock()

            # readonly mount
            isdir.return_value = True
            bind(src, dest, chroot, create=True, readonly=True)
            call1 = mock.call(source=src, target=dest, fstype='none', flags=(MS_BIND), data='')
            call2 = mock.call(source=src, target=dest, fstype='none', flags=(MS_BIND | MS_REMOUNT | MS_RDONLY), data='')
            mount.assert_has_calls([call1, call2])

            #with raises(MountError):
                #bind('/', '/root', readonly=True)
        finally:
            shutil.rmtree(src)
            shutil.rmtree(chroot)

from itertools import chain, cycle
import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock
from pytest import raises

from chroot import Chroot
from chroot.exceptions import ChrootError, ChrootMountError
from chroot.utils import MountError


def test_Chroot():
    if sys.hexversion >= 0x03030000:
        patcher = mock.patch('chroot.sethostname')
        sethostname = patcher.start()

    # testing Chroot.mount()
    with mock.patch('os.geteuid', return_value=0), \
            mock.patch('chroot.bind') as bind, \
            mock.patch('os.path.exists') as exists, \
            mock.patch('chroot.dictbool') as dictbool, \
            mock.patch('chroot.simple_unshare'):

        c = Chroot('/')
        with raises(ChrootMountError):
            c.mount()

        bind.side_effect = MountError('fake exception')
        c.unshare()
        with raises(ChrootMountError):
            c.mount()

        bind.reset_mock()
        bind.side_effect = None
        exists.return_value = False
        dictbool.return_value = True
        c.mount()
        assert not bind.called

    with mock.patch('os.geteuid') as geteuid, \
            mock.patch('os.fork') as fork, \
            mock.patch('os.chroot') as chroot, \
            mock.patch('os.chdir') as chdir, \
            mock.patch('os.remove') as remove, \
            mock.patch('os._exit') as exit, \
            mock.patch('os.path.exists') as exists, \
            mock.patch('os.waitpid') as waitpid, \
            mock.patch('chroot.Chroot.mount') as mount, \
            mock.patch('chroot.simple_unshare'):

        geteuid.return_value = 1

        # not running as root
        with raises(ChrootError):
            chroot = Chroot('/')

        geteuid.return_value = 0

        # invalid hostname
        with raises(ChrootError):
            Chroot('/', hostname=True)

        # bad path
        exists.return_value = False
        with raises(ChrootError):
            Chroot('/nonexistent/path')
        exists.return_value = True

        # $FAKEPATH not defined in environment
        with raises(ChrootMountError):
            Chroot('/', mountpoints={'$FAKEVAR': {}})

        with mock.patch('chroot.os.getenv', return_value='/fake/src/path'):
            Chroot('/', mountpoints={'$FAKEVAR': {}})

        # test parent process
        fork.return_value = 10

        c = Chroot('/', hostname='test')
        with c:
            pass

        # test child process
        fork.return_value = 0

        c = Chroot('/')
        with c:
            pass

        # make sure the default mount points aren't altered
        # when passing custom mount points
        default_mounts = Chroot.default_mounts.copy()
        c = Chroot('/', mountpoints={'tmpfs': {'dest': '/tmp'}})
        assert default_mounts == c.default_mounts

        remove.side_effect = Exception('fake exception')
        exists.side_effect = chain([True], cycle([False]))
        c = Chroot('/', mountpoints={'/root': {'dest': '/blah'}})
        with raises(ChrootMountError):
            with c:
                pass
        remove.side_effect = None
        exists.side_effect = None

        chdir.side_effect = Exception('fake exception')
        with c:
            pass
        chdir.side_effect = None

        mock.patch.stopall()

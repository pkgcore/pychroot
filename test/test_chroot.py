from itertools import chain, cycle
import os
import sys

if sys.hexversion >= 0x03030000:
    from unittest.mock import Mock, patch
else:
    from mock import Mock, patch
from pytest import raises

from chroot import Chroot
from chroot.exceptions import ChrootError, ChrootMountError
from chroot.utils import MountError


def test_Chroot():
    if sys.hexversion >= 0x03030000:
        patcher = patch('chroot.sethostname')
        sethostname = patcher.start()

    # testing Chroot.mount()
    with patch('chroot.os.geteuid', return_value=0), \
            patch('chroot.bind') as bind, \
            patch('chroot.exists') as exists, \
            patch('chroot.dictbool') as dictbool, \
            patch('chroot.unshare') as unshare:

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

    with patch('chroot.os.geteuid') as geteuid, \
            patch('chroot.os.fork') as fork, \
            patch('chroot.os.chroot') as chroot, \
            patch('chroot.os.chdir') as chdir, \
            patch('chroot.os.remove') as remove, \
            patch('chroot.os._exit') as exit, \
            patch('chroot.exists') as exists, \
            patch('chroot.Chroot.mount') as mount, \
            patch('chroot.os.waitpid') as waitpid, \
            patch('chroot.unshare') as unshare:

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

        with patch('chroot.os.getenv', return_value='/fake/src/path'):
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

        patch.stopall()

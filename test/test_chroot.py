from __future__ import unicode_literals

from itertools import chain, cycle

try:
    from unittest import mock
except ImportError:
    import mock
from pytest import raises

from pychroot.base import Chroot
from pychroot.exceptions import ChrootError, ChrootMountError


def test_Chroot():
    # testing Chroot.mount()
    with mock.patch('pychroot.base.bind') as bind, \
            mock.patch('os.path.exists') as exists, \
            mock.patch('pychroot.base.dictbool') as dictbool, \
            mock.patch('pychroot.base.simple_unshare'):

        chroot = Chroot('/')
        bind.side_effect = None
        exists.return_value = False
        dictbool.return_value = True
        chroot.mount()
        assert not bind.called

    with mock.patch('os.fork') as fork, \
            mock.patch('os.chroot'), \
            mock.patch('os.chdir') as chdir, \
            mock.patch('os.remove') as remove, \
            mock.patch('os._exit'), \
            mock.patch('os.path.exists') as exists, \
            mock.patch('os.waitpid'), \
            mock.patch('pychroot.utils.mount'), \
            mock.patch('pychroot.base.simple_unshare'):

        # bad path
        exists.return_value = False
        with raises(ChrootError):
            Chroot('/nonexistent/path')
        exists.return_value = True

        # $FAKEPATH not defined in environment
        with raises(ChrootMountError):
            Chroot('/', mountpoints={'$FAKEVAR': {}})

        # optional, undefined variable mounts get dropped
        chroot = Chroot('/', mountpoints={
            '$FAKEVAR': {'optional': True},
            '/home/user': {}})
        assert '$FAKEVAR' not in chroot.mounts
        assert len(list(chroot.mounts)) - len(chroot.default_mounts) == 1

        with mock.patch('os.getenv', return_value='/fake/src/path'):
            Chroot('/', mountpoints={'$FAKEVAR': {}})

        # test parent process
        fork.return_value = 10

        chroot = Chroot('/', hostname='test')
        with chroot:
            pass

        # test child process
        fork.return_value = 0

        chroot = Chroot('/')
        with chroot:
            pass

        # make sure the default mount points aren't altered
        # when passing custom mount points
        default_mounts = Chroot.default_mounts.copy()
        chroot = Chroot('/', mountpoints={'tmpfs:/tmp': {}})
        assert default_mounts == chroot.default_mounts

        remove.side_effect = Exception('fake exception')
        exists.side_effect = chain([True], cycle([False]))
        chroot = Chroot('/', mountpoints={'/root:/blah': {}})
        with raises(ChrootMountError):
            with chroot:
                pass
        remove.side_effect = None
        exists.side_effect = None

        chdir.side_effect = Exception('fake exception')
        with chroot:
            pass
        chdir.side_effect = None

        mock.patch.stopall()

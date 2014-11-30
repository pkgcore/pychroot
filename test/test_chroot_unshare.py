try:
    from unittest import mock
except ImportError:
    import mock
from mock import Mock, patch
from pytest import raises

from chroot import unshare
from chroot.unshare import CLONE_NEWUSER


def test_unshare():
    # most unshare calls require elevated privs, CLONE_NEWUSER doesn't
    #unshare(CLONE_NEWUSER)

    # force an unshare failure
    with patch('ctypes.CDLL') as mocked_ctypes:
        mocked_ctypes.unshare = Mock(return_value=1)
        with raises(OSError):
            unshare(CLONE_NEWUSER)

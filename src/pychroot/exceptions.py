"""Various chroot-related exception classes"""

import os


class ChrootError(Exception):
    """Exception raised when there is an error setting up a chroot."""

    def __init__(self, msg, errno=None):
        self.msg = msg
        self.errno = errno

    def __str__(self):
        error = [self.msg]
        if self.errno is not None:
            error.append(os.strerror(self.errno))
        return ': '.join(error)


class ChrootMountError(ChrootError):
    """Exception raised when there is an error setting up chroot bind mounts."""

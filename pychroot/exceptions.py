"""Various chroot-related exception classes"""

from __future__ import unicode_literals

import os


class ChrootError(Exception):

    """Exception that is raised when there is an error when trying to set up a chroot."""
    def __init__(self, message, errno=None):
        self.message = message
        self.args = (message,)

        if errno is not None:
            self.errno = errno
            self.strerror = os.strerror(errno)

    def __str__(self):
        error_messages = [self.message]
        if getattr(self, 'strerror', False):
            error_messages.append(self.strerror)
        return ': '.join(error_messages)


class ChrootMountError(ChrootError):

    """Exception that is raised when there is an error trying to set up the bind mounts for a chroot."""
    pass

"""Various chroot-related exception classes"""

import os


class ChrootError(Exception):
    """Exception raised when there is an error setting up a chroot."""

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
    """Exception raised when there is an error setting up chroot bind mounts."""

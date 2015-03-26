"""Various chroot-related exception classes"""


class ChrootError(Exception):

    """Exception that is raised when there is an error when trying to set up a chroot."""
    pass


class ChrootMountError(ChrootError):

    """Exception that is raised when there is an error trying to set up the bind mounts for a chroot."""
    pass


class MountError(Exception):

    """Exception that is raised when there is an error creating a bind mount."""
    pass

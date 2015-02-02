"""Various chroot-related utilities mostly dealing with bind mounting."""

import ctypes
import ctypes.util
import errno
import logging
import operator
import os

try:
    # py3 moved reduce into functools
    from functools import reduce  # pylint: disable=redefined-builtin
except ImportError:
    pass

from chroot.exceptions import MountError


def dictbool(dct, key):
    """Check if a key exists and is True in a dictionary.

    :param dct: The dictionary to check.
    :type dct: dict
    :param key: The key to check
    :type key: any
    """
    return key in dct and isinstance(dct[key], bool) and dct[key]


def getlogger(log, name):
    """Gets a logger given a logger and a package.

    Will return the given logger if the name is not generated from
    the current package, otherwise generate a logger based on __name__.

    :param log: Logger to start with.
    :type log: logging.Logger
    :param name: The __name__ of the caller.
    :type name: str
    """
    return (
        log if isinstance(log, logging.Logger)
        and not log.name.startswith(name.partition('.')[0])
        else logging.getLogger(name))


def bind(src, dest, create=False, log=None, readonly=False,
         recursive=False, **_kwargs):
    """Set up a bind mount.

    :param src: The source location to mount.
    :type src: str
    :param dest: The destination to mount on.
    :type dest: str
    :param create: Whether to create the destination.
    :type create: bool
    :param log: A logger to use for logging.
    :type log: logging.Logger
    :param readonly: Whether to remount read-only.
    :type readonly: bool
    :param recursive: Whether to use a recursive bind mount.
    :type recursive: bool
    """
    log = getlogger(log, __name__)
    fstypes = ('proc', 'sysfs', 'tmpfs')
    mount_flags = []
    mount_options = []

    if src not in fstypes:
        src = os.path.realpath(src)
    dest = os.path.realpath(dest)

    if create:
        try:
            if not os.path.isdir(src) and src not in fstypes:
                os.makedirs(os.path.dirname(dest))
            else:
                os.makedirs(dest)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if not os.path.isdir(src) and src not in fstypes:
            open(dest, 'w').close()

    if not os.path.exists(src) and src not in fstypes:
        raise MountError('Attempt to bind mount nonexistent source path "{}"'.format(src))
    elif not os.path.exists(dest):
        raise MountError('Attempt to bind mount on nonexistent path "{}"'.format(dest))

    if src in fstypes:
        fstype = src
        log.debug("  mounting '{}' filesystem on '{}'".format(src, dest))
    else:
        fstype = 'none'
        mount_flags.append(MS_BIND)
        if recursive:
            mount_flags.append(MS_REC)
        log.debug("  bind mounting '{}' on '{}'".format(src, dest))

    try:
        mount(source=src, target=dest, fstype=fstype,
              flags=reduce(operator.or_, mount_flags, 0),
              data=','.join(mount_options))
        if readonly:
            mount_flags.extend([MS_REMOUNT, MS_RDONLY])
            mount(source=src, target=dest, fstype=fstype,
                  flags=reduce(operator.or_, mount_flags, 0),
                  data=','.join(mount_options))
    except OSError as e:
        raise MountError(e)

# Flags synced from sys/mount.h.  See mount(2) for details.
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_NOEXEC = 8
MS_SYNCHRONOUS = 16
MS_REMOUNT = 32
MS_MANDLOCK = 64
MS_DIRSYNC = 128
MS_NOATIME = 1024
MS_NODIRATIME = 2048
MS_BIND = 4096
MS_MOVE = 8192
MS_REC = 16384
MS_SILENT = 32768
MS_POSIXACL = 1 << 16
MS_UNBINDABLE = 1 << 17
MS_PRIVATE = 1 << 18
MS_SLAVE = 1 << 19
MS_SHARED = 1 << 20
MS_RELATIME = 1 << 21
MS_KERNMOUNT = 1 << 22
MS_I_VERSION = 1 << 23
MS_STRICTATIME = 1 << 24
MS_ACTIVE = 1 << 30
MS_NOUSER = 1 << 31


def mount(source, target, fstype, flags, data=None):
    """Call the mount(2) func; see the man page for details."""
    libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
    if libc.mount(source.encode(), target.encode(),
                  fstype.encode(), ctypes.c_ulong(flags), data) != 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))

"""Various chroot-related utilities mostly dealing with bind mounting."""

import errno
from functools import reduce  # pylint: disable=redefined-builtin
import logging
import operator
import os

from snakeoil.fileutils import touch
from snakeoil.osutils.mount import mount, MS_BIND, MS_REC, MS_REMOUNT, MS_RDONLY

from .exceptions import ChrootMountError


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


def bind(src, dest, chroot, create=False, log=None, readonly=False,
         recursive=False, **_kwargs):
    """Set up a bind mount.

    :param src: The source location to mount.
    :type src: str
    :param dest: The destination to mount on.
    :type dest: str
    :param chroot: The chroot base path.
    :type chroot: str
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
        src = os.path.normpath(src)
    if os.path.islink(dest):
        dest = os.path.join(chroot, os.path.realpath(dest).lstrip('/'))
        if not os.path.exists(dest):
            create = True
    else:
        dest = os.path.normpath(dest)

    if create:
        try:
            if not os.path.isdir(src) and src not in fstypes:
                os.makedirs(os.path.dirname(dest))
            else:
                os.makedirs(dest)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        if not os.path.isdir(src) and src not in fstypes:
            try:
                touch(dest)
            except OSError as e:
                raise ChrootMountError(
                    f'cannot bind mount to {dest!r}', getattr(e, 'errno', None))

    if not os.path.exists(src) and src not in fstypes:
        raise ChrootMountError(f'cannot bind mount from {src!r}', errno.ENOENT)
    elif not os.path.exists(dest):
        raise ChrootMountError(f'cannot bind mount to {dest!r}', errno.ENOENT)

    if src in fstypes:
        fstype = src
        log.debug('  mounting %r filesystem on %r', src, dest)
    else:
        fstype = None
        mount_flags.append(MS_BIND)
        if recursive:
            mount_flags.append(MS_REC)
        log.debug('  bind mounting %r on %r', src, dest)

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
        raise ChrootMountError(
            f'failed mounting: mount -t {fstype} {src} {dest}', e.errno)

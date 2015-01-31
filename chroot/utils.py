import errno
import logging
import os

from subprocess import call
try:
    from libmount import Context
except ImportError:
    Context = None

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


def bind(src, dest, create=False, log=None, recursive=False, **_kwargs):
    """Set up a bind mount.

    :param src: The source location to mount.
    :type src: str
    :param dest: The destination to mount on.
    :type dest: str
    :param create: Whether to create the destination.
    :type create: bool
    :param log: A logger to use for logging.
    :type log: logging.Logger
    :param recursive: Whether to use a recursive bind mount.
    :type recursive: bool
    """
    log = getlogger(log, __name__)
    if src not in ['proc', 'sysfs', 'tmpfs']:
        src = os.path.realpath(src)
    dest = os.path.realpath(dest)

    if create:
        try:
            if not os.path.isdir(src) and src not in ['proc', 'sysfs', 'tmpfs']:
                os.makedirs(os.path.dirname(dest))
            else:
                os.makedirs(dest)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if not os.path.isdir(src) and src not in ['proc', 'sysfs', 'tmpfs']:
            open(dest, 'w').close()

    if not os.path.exists(src) and src not in ['proc', 'sysfs', 'tmpfs']:
        raise MountError('Attempt to bind mount nonexistent source path "{}"'.format(src))
    elif not os.path.exists(dest):
        raise MountError('Attempt to bind mount on nonexistent path "{}"'.format(dest))

    if src in ['proc', 'sysfs', 'tmpfs']:
        fstype = src
        mount_options = []
        log.debug("  mounting '{}' filesystem on '{}'".format(src, dest))
    else:
        fstype = 'none'
        mount_options = ['rbind' if recursive else 'bind']
        log.debug("  bind mounting '{}' on '{}'".format(src, dest))

    if Context is not None:
        context = Context(source=src, target=dest, fstype=fstype, options=','.join(mount_options))
        try:
            context.mount()
        except Exception as ex:
            raise MountError(str(ex))
    else:
        status = call(['mount', '--no-mtab', '--types', fstype, '--options', ','.join(mount_options), src, dest])

        if status != 0:
            raise MountError('Mount failed')


# vim:et:ts=4:sw=4:tw=120:sts=4:ai:

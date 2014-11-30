
__version__ = '0.9.6'

import os
from os.path import abspath, normpath, join, exists, basename
import sys

# pylint: disable=E0611
# python-3.3 not yet supported in pylint
if sys.hexversion >= 0x03030000:
    from socket import sethostname

# make sure that we are in sys.path
if abspath(normpath(join(__file__, '../..'))) not in sys.path:
    sys.path.append(abspath(normpath(join(__file__, '../..'))))

from chroot.unshare import unshare, CLONE_NEWUTS, CLONE_NEWNS, CLONE_NEWIPC  # pylint: disable=F0401
# pylint likely will not see this stuff..

from chroot.base import WithParentSkip
from chroot.definitions import DEFAULT_MOUNTS
from chroot.exceptions import ChrootError, ChrootMountError
from chroot.utils import bind, MountError, getlogger, dictbool


class Chroot(WithParentSkip):

    """Context Manager class that implements running the contents of the with-context in a chroot.

    This is done by forking, doing some magic on the stack so the contents are not executed in the parent,
    and executing the context in the forked child. Exceptions are pickled and passed through to the parent.

    :param path: The path to the image to chroot into.
    :type path: str
    :param log: A log object to use for logging.
    :type log: logging.Logger
    :param mountpoints: A dictionary defining the mountpoints to use. These can override any of the defaults
                        or add extra mountpoints
    :type mountpoints: dict
    :param hostname: The hostname to use in the chroot. If left blank then the basename of the path is used.
    :type hostname: str
    """

    def __init__(self, path, log=None, mountpoints=None, hostname=None):
        self.log = getlogger(log, __name__)

        # TODO: capabilities check as well?
        # see http://marc.info/?l=python-dev&m=116406900432743
        if os.geteuid() != 0:
            raise ChrootError('Cannot use chroot module when not running as root')
        elif hostname is not None and not isinstance(hostname, str):
            raise ChrootError('Hostname parameter passed a non-string object')

        super(Chroot, self).__init__()
        self.__unshared = False

        if not exists(abspath(path)):
            raise ChrootError('Attempt to chroot into a nonexistent path')

        self.path = abspath(path)
        self.mountpoints = DEFAULT_MOUNTS
        self.mountpoints.update(mountpoints if mountpoints else {})

        # flag mount points that require creation and removal
        for mount, chrmount, opts in ((m, join(self.path, o['dest'].lstrip('/')) if 'dest' in o else
                                       join(self.path, m.lstrip('/')), o) for m, o in self.mountpoints.items()):
            src = mount
            # expand mountpoints that are environment variables
            if mount.startswith('$'):
                src = os.getenv(mount[1:])
                if src is None:
                    raise ChrootMountError('Environment variable "{}" is not defined in '
                                           'the host environment'.format(mount))
                self.log.debug('Expanding mountpoint "%s" to "%s"', mount, src)
                self.mountpoints[src] = opts
                del self.mountpoints[mount]
                if '$' in chrmount:
                    chrmount = join(self.path, src.lstrip('/'))

            if not 'optional' in opts and not exists(chrmount):
                self.mountpoints[src]['create'] = True

        if hostname is not None:
            self.hostname = hostname
            if sys.hexversion < 0x03030000:
                self.log.warn('Unable to set hostname on Python < 3.3')
        else:
            self.hostname = basename(self.path)

    def child_setup(self):
        self.unshare()
        self.mount()
        os.chroot(self.path)
        os.chdir('/')

    def cleanup(self):
        # remove mount points that were dynamically created
        for chrmount in (join(self.path, o['dest'].lstrip('/')) if 'dest' in o else
                         join(self.path, m.lstrip('/')) for m, o in self.mountpoints.items()
                         if 'create' in o):
            self.log.debug('Removing dynamically created mountpoint "%s"', chrmount)
            try:
                if not os.path.isdir(chrmount):
                    os.remove(chrmount)
                    chrmount = os.path.dirname(chrmount)
                os.removedirs(chrmount)
            # don't fail if leaf directories aren't empty when trying to remove them
            except OSError:
                pass
            except:
                raise ChrootMountError('Failed to remove chroot mount point "{}"'.format(chrmount))

    def unshare(self):
        """
        Use Linux namespaces to add the current process to a new UTS (hostname) namespace, new
        mount namespace and new IPC namespace.
        """
        unshare(CLONE_NEWUTS | CLONE_NEWNS | CLONE_NEWIPC)

        # set the hostname in the chroot process to hostname for the chroot
        if sys.hexversion >= 0x03030000:
            sethostname(self.hostname)

        self.__unshared = True

    def mount(self):
        """Do the bind mounts for this chroot object. This _must_ be run after unshare."""
        if not self.__unshared:
            raise ChrootMountError('Attempted to run mount method without running unshare method')

        for mount, chrmount, opts in ((m, join(self.path, o['dest'].lstrip('/')) if 'dest' in o else
                                       join(self.path, m.lstrip('/')), o) for m, o in self.mountpoints.items()
                                      if not m.startswith('$')):

            if dictbool(opts, 'optional') and not exists(mount):
                self.log.debug('Not mounting "%s" as it\'s optional and doesn\'t exist', mount)
                continue

            try:
                kwargs = {k: v for k, v in opts.items() if k != 'dest'}
                bind(src=mount, dest=chrmount, log=self.log, **kwargs)
            except MountError as ex:
                raise ChrootMountError(str(ex))


# vim:et:ts=4:sw=4:tw=120:sts=4:ai:

"""pychroot is a library that simplifies chroot handling"""

import os
import sys

if sys.hexversion >= 0x03030000:
    from socket import sethostname  # pylint: disable=no-name-in-module

from chroot.base import WithParentSkip
from chroot.exceptions import ChrootError, ChrootMountError, MountError
from chroot.utils import bind, getlogger, dictbool
from chroot._version import __version__

from snakeoil.namespaces import simple_unshare


class Chroot(WithParentSkip):

    """Context manager that provides chroot support.

    This is done by forking, doing some magic on the stack so the contents are
    not executed in the parent, and executing the context in the forked child.
    Exceptions are pickled and passed through to the parent.

    :param path: The path to the image to chroot into.
    :type path: str
    :param log: A log object to use for logging.
    :type log: logging.Logger
    :param mountpoints: A dictionary defining the mountpoints to use. These can
        override any of the defaults or add extra mountpoints
    :type mountpoints: dict
    :param hostname: The hostname to use in the chroot. If left blank then the
        basename of the path is used.
    :type hostname: str
    """

    default_mounts = {
        '/dev': {
            'recursive': True,
            'readonly': True,
        },
        'proc': {'dest': '/proc'},
        'sysfs': {'dest': '/sys'},
        'tmpfs': {'dest': '/dev/shm'},
        '/etc/resolv.conf': {},
    }

    def __init__(self, path, log=None, mountpoints=None, hostname=None):
        self.log = getlogger(log, __name__)

        # TODO: capabilities check as well?
        # see http://marc.info/?l=python-dev&m=116406900432743
        if os.geteuid() != 0:
            raise ChrootError('Must have root permissions to use chroot')
        elif hostname is not None and not isinstance(hostname, str):
            raise ChrootError('Hostname parameter passed a non-string object')

        super(Chroot, self).__init__()
        self.__unshared = False

        if not os.path.exists(os.path.abspath(path)):
            raise ChrootError('Attempt to chroot into a nonexistent path')

        self.path = os.path.abspath(path)
        self.mountpoints = self.default_mounts.copy()
        self.mountpoints.update(mountpoints if mountpoints else {})

        # flag mount points that require creation and removal
        for mount, chrmount, opts in self.mounts:
            src = mount
            # expand mountpoints that are environment variables
            if mount.startswith('$'):
                src = os.getenv(mount[1:])
                if src is None:
                    raise ChrootMountError(
                        'Host environment variable undefined: {}'.format(mount))
                self.log.debug('Expanding mountpoint "%s" to "%s"', mount, src)
                self.mountpoints[src] = opts
                del self.mountpoints[mount]
                if '$' in chrmount:
                    chrmount = os.path.join(self.path, src.lstrip('/'))

            if 'optional' not in opts and not os.path.exists(chrmount):
                self.mountpoints[src]['create'] = True

        if hostname is not None:
            self.hostname = hostname
            if sys.hexversion < 0x03030000:
                self.log.warn('Unable to set hostname on Python < 3.3')
        else:
            self.hostname = os.path.basename(self.path)

    @property
    def mounts(self):
        for source, options in self.mountpoints.items():
            if 'dest' in options:
                dest = os.path.join(self.path, options['dest'].lstrip('/'))
            else:
                dest = os.path.join(self.path, source.lstrip('/'))
            yield source, dest, options

    def child_setup(self):
        self.unshare()
        self.mount()
        os.chroot(self.path)
        os.chdir('/')

    def cleanup(self):
        # remove mount points that were dynamically created
        for _, chrmount, opts in self.mounts:
            if 'create' not in opts:
                continue
            self.log.debug('Removing dynamically created mountpoint: %s', chrmount)
            try:
                if not os.path.isdir(chrmount):
                    os.remove(chrmount)
                    chrmount = os.path.dirname(chrmount)
                os.removedirs(chrmount)
            # don't fail if leaf directories aren't empty when trying to remove them
            except OSError:
                pass
            except:
                raise ChrootMountError('Failed to remove chroot mount point: {}'.format(chrmount))

    def unshare(self):
        """
        Use Linux namespaces to add the current process to a new UTS (hostname)
        namespace, new mount namespace and new IPC namespace.
        """
        simple_unshare(pid=True)

        # set the hostname in the chroot process to hostname for the chroot
        if sys.hexversion >= 0x03030000:
            sethostname(self.hostname)

        self.__unshared = True

    def mount(self):
        """Do the bind mounts for this chroot object.

        This _must_ be run after unshare.
        """
        if not self.__unshared:
            raise ChrootMountError('Attempted to run mount method without running unshare method')

        for mount, chrmount, opts in self.mounts:
            if mount.startswith('$'):
                continue
            if dictbool(opts, 'optional') and not os.path.exists(mount):
                self.log.debug('Skipping optional and nonexistent mountpoint: %s', mount)
                continue
            try:
                kwargs = {k: v for k, v in opts.items() if k != 'dest'}
                bind(src=mount, dest=chrmount, chroot=self.path, log=self.log, **kwargs)
            except MountError as ex:
                raise ChrootMountError(str(ex))

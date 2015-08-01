import errno
import os
import socket
import sys

from pychroot.exceptions import ChrootError, ChrootMountError
from pychroot.utils import bind, getlogger, dictbool

from snakeoil.contextlib import SplitExec
from snakeoil.namespaces import simple_unshare


class Chroot(SplitExec):

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
    :param hostname: The hostname for the chroot, defaults to the system
    hostname. In order to set the chroot domain name as well specify an
        FQDN instead of a singular hostname.
    :type hostname: str
    """

    default_mounts = {
        '/dev': {
            'recursive': True,
            'readonly': True,
        },
        '/proc': {},
        '/sys': {},
        'tmpfs:/dev/shm': {},
        '/etc/resolv.conf': {},
    }

    def __init__(self, path, log=None, mountpoints=None, hostname=None):
        self.log = getlogger(log, __name__)

        # TODO: capabilities check as well?
        # see http://marc.info/?l=python-dev&m=116406900432743
        if os.geteuid() != 0:
            raise ChrootError(
                "cannot change root directory to '{}'".format(path), errno.EPERM)

        if not os.path.isdir(os.path.abspath(path)):
            raise ChrootError(
                "cannot change root directory to '{}'".format(path), errno.ENOTDIR)

        super(Chroot, self).__init__()
        self.path = os.path.abspath(path)
        self.hostname = hostname
        self.mountpoints = self.default_mounts.copy()
        self.mountpoints.update(mountpoints if mountpoints else {})

        # flag mount points that require creation and removal
        for k, source, chrmount, opts in self.mounts:
            src = source
            # expand mountpoints that are environment variables
            if source.startswith('$'):
                src = os.getenv(source[1:], source)
                if src == source:
                    if 'optional' in opts:
                        self.log.debug(
                            'Skipping optional and nonexistent mountpoint '
                            'due to undefined host environment variable: %s', source)
                        del self.mountpoints[k]
                        continue
                    else:
                        raise ChrootMountError(
                            'cannot mount undefined environment variable: {}'.format(source))
                self.log.debug('Expanding mountpoint "%s" to "%s"', source, src)
                self.mountpoints[src] = opts
                del self.mountpoints[k]
                if '$' in chrmount:
                    chrmount = os.path.join(self.path, src.lstrip('/'))

            if 'optional' not in opts and not os.path.exists(chrmount):
                self.mountpoints[k]['create'] = True

    @property
    def mounts(self):
        for k, options in self.mountpoints.items():
            source, _, dest = k.partition(':')
            if not dest:
                dest = source
            dest = os.path.join(self.path, dest.lstrip('/'))
            yield k, source, dest, options

    def child_setup(self):
        simple_unshare(pid=True, hostname=self.hostname)
        self.mount()
        os.chroot(self.path)
        os.chdir('/')

    def cleanup(self):
        # remove mount points that were dynamically created
        for _, _, chrmount, opts in self.mounts:
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
            except Exception as e:
                raise ChrootMountError(
                    "failed to remove chroot mount point '{}'".format(chrmount), getattr(e, 'errno', None))

    def mount(self):
        """Do the bind mounts for this chroot object.

        This _must_ be run after creating a new mount namespace.
        """
        for _, source, chrmount, opts in self.mounts:
            if dictbool(opts, 'optional') and not os.path.exists(source):
                self.log.debug('Skipping optional and nonexistent mountpoint: %s', source)
                continue
            bind(src=source, dest=chrmount, chroot=self.path, log=self.log, **opts)

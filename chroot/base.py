import os
import sys

if sys.hexversion >= 0x03030000:
    from socket import sethostname  # pylint: disable=no-name-in-module

from chroot.exceptions import ChrootError, ChrootMountError, MountError
from chroot.utils import bind, getlogger, dictbool

from snakeoil.contextlib import SplitExec
from snakeoil.namespaces import simple_unshare
from snakeoil.osutils import mount, MS_REC, MS_SLAVE


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
    :param hostname: The hostname to use in the chroot. If left blank then the
        basename of the path is used.
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
        for k, source, chrmount, opts in self.mounts:
            src = source
            # expand mountpoints that are environment variables
            if source.startswith('$'):
                src = os.getenv(source[1:])
                if src is None:
                    raise ChrootMountError(
                        'Host environment variable undefined: {}'.format(source))
                self.log.debug('Expanding mountpoint "%s" to "%s"', source, src)
                self.mountpoints[src] = opts
                del self.mountpoints[k]
                if '$' in chrmount:
                    chrmount = os.path.join(self.path, src.lstrip('/'))

            if 'optional' not in opts and not os.path.exists(chrmount):
                self.mountpoints[k]['create'] = True

        if hostname is not None:
            self.hostname = hostname
            if sys.hexversion < 0x03030000:
                self.log.warn('Unable to set hostname on Python < 3.3')
        else:
            self.hostname = os.path.basename(self.path)

    @property
    def mounts(self):
        for k, options in self.mountpoints.items():
            source, _, dest = k.partition(':')
            if not dest:
                dest = source
            dest = os.path.join(self.path, dest.lstrip('/'))
            yield k, source, dest, options

    def child_setup(self):
        self.unshare()
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

        # Allow mount propagation from the host to chroot namespace, but not
        # from chroot to host.
        mount('none', '/', 'none', MS_REC | MS_SLAVE)

        for _, source, chrmount, opts in self.mounts:
            if source.startswith('$'):
                continue
            if dictbool(opts, 'optional') and not os.path.exists(source):
                self.log.debug('Skipping optional and nonexistent mountpoint: %s', source)
                continue
            try:
                bind(src=source, dest=chrmount, chroot=self.path, log=self.log, **opts)
            except MountError as e:
                raise ChrootMountError(e)

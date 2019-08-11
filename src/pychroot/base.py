import errno
import os

from snakeoil.contexts import SplitExec
from snakeoil.process.namespaces import simple_unshare

from .exceptions import ChrootError, ChrootMountError
from .utils import bind, getlogger, dictbool


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
        '/dev': {'recursive': True},
        'proc:/proc': {},
        'sysfs:/sys': {},
        'tmpfs:/dev/shm': {},
        '/etc/resolv.conf': {},
    }

    def __init__(self, path, log=None, mountpoints=None, hostname=None, skip_chdir=False):
        super(Chroot, self).__init__()
        self.log = getlogger(log, __name__)
        self.path = os.path.abspath(path)
        self.hostname = hostname
        self.skip_chdir = skip_chdir
        self.mountpoints = self.default_mounts.copy()
        self.mountpoints.update(mountpoints if mountpoints else {})

        if not os.path.isdir(self.path):
            raise ChrootError(f'cannot change root directory to {path!r}', errno.ENOTDIR)

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
                            f'cannot mount undefined environment variable: {source}')
                self.log.debug('Expanding mountpoint %r to %r', source, src)
                self.mountpoints[src] = opts
                del self.mountpoints[k]
                k = src
                if '$' in chrmount:
                    chrmount = os.path.join(self.path, src.lstrip('/'))

            if 'optional' not in opts and not os.path.exists(chrmount):
                self.mountpoints[k]['create'] = True

    @property
    def mounts(self):
        for k, options in list(self.mountpoints.items()):
            source, _, dest = k.partition(':')
            if not dest:
                dest = source
            dest = os.path.join(self.path, dest.lstrip('/'))
            yield k, source, dest, options

    def _child_setup(self):
        kwargs = {}
        if os.getuid() != 0:
            # Enable a user namespace if we're not root. Note that this also
            # requires a network namespace in order to mount sysfs and use
            # network devices; however, we currently only provide a basic
            # loopback interface if iproute2 is installed in the chroot so
            # regular connections out of the namespaced environment won't work
            # by default.
            kwargs.update({'user': True, 'net': True})

        simple_unshare(pid=True, hostname=self.hostname, **kwargs)
        self._mount()
        os.chroot(self.path)
        if not self.skip_chdir:
            os.chdir('/')

    def _cleanup(self):
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
                    f'failed to remove chroot mount point {chrmount!r}',
                    getattr(e, 'errno', None))

    def _mount(self):
        """Do the bind mounts for this chroot object.

        This _must_ be run after creating a new mount namespace.
        """
        for _, source, chrmount, opts in self.mounts:
            if dictbool(opts, 'optional') and not os.path.exists(source):
                self.log.debug('Skipping optional and nonexistent mountpoint: %s', source)
                continue
            bind(src=source, dest=chrmount, chroot=self.path, log=self.log, **opts)

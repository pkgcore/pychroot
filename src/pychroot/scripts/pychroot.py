"""an extended chroot equivalent

pychroot is an extended **chroot(1)** equivalent that also provides support for
automatically handling bind mounts. By default, the proc and sysfs filesystems
are mounted to their respective /proc and /sys locations inside the chroot as
well as bind mounting /dev and /etc/resolv.conf from the host system.

In addition to the defaults, the user is able to specify custom bind mounts.
For example, the following command will recursively bind mount the user's home
directory at the same location inside the chroot directory::

    pychroot -R /home/user ~/chroot

This allows a user to easily set up a custom chroot environment without having
to resort to scripted mount handling or other methods.
"""

import argparse
from functools import partial
import os
import subprocess

from snakeoil.cli import arghparse

from ..base import Chroot
from ..exceptions import ChrootError


def bindmount(s, recursive=False, readonly=False):
    """Argparse argument type for bind mount variants."""
    opts = {'recursive': recursive, 'readonly': readonly}
    return {s: opts}


class mountpoints(argparse.Action):
    """Argparse action that adds specified mountpoint to be mounted."""

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, 'mountpoints', False):
            namespace.mountpoints = {}
        namespace.mountpoints.update(values)


argparser = arghparse.ArgumentParser(
    color=False, debug=False, quiet=False, verbose=False,
    description=__doc__, script=(__file__, __name__))
argparser.add_argument('path', help='path to newroot')
argparser.add_argument(
    'command', nargs=argparse.REMAINDER, help='optional command to run',
    docs="""
        Optional command to run.

        Similar to chroot(1), if unspecified this defaults to $SHELL from the
        host environment and if that's unset it executes /bin/sh.
    """)

chroot_options = argparser.add_argument_group('chroot options')
chroot_options.add_argument(
    '--no-mounts', action='store_true',
    help='disable the default bind mounts',
    docs="""
        Disable the default bind mounts which can be used to obtain a standard
        chroot environment that you'd expect when using chroot(1).
    """)
chroot_options.add_argument(
    '--hostname', type=str, help='specify the chroot hostname',
    docs="""
        Specify the chroot hostname. In order to set the domain name as well,
        pass an FQDN instead of a singular hostname.
    """)
chroot_options.add_argument(
    '--skip-chdir', action='store_true',
    help="do not change working directory to '/'",
    docs="""
        Do not change the current working directory to '/'.

        Unlike chroot(1), this currently doesn't limit you to only using it
        when the new root isn't '/'. In other words, you can use a new chroot
        environment on the current host system rootfs with one caveat: any
        absolute paths will use the new rootfs.
    """)
chroot_options.add_argument(
    '-B', '--bind', type=bindmount, action=mountpoints,
    metavar='SRC[:DEST]', help='specify custom bind mount',
    docs="""
        Specify a custom bind mount.

        In order to mount the same source to multiple destinations, use the
        SRC:DEST syntax. For example, the following will bind mount '/srv/data'
        to /srv/data and /home/user/data in the chroot::

            pychroot -B /srv/data -B /srv/data:/home/user/data /path/to/chroot
    """)
chroot_options.add_argument(
    '-R', '--rbind', type=partial(bindmount, recursive=True),
    action=mountpoints, metavar='SRC[:DEST]',
    help='specify custom recursive bind mount')
chroot_options.add_argument(
    '--ro', '--readonly', type=partial(bindmount, readonly=True),
    action=mountpoints, metavar='SRC[:DEST]',
    help='specify custom readonly bind mount',
    docs="""
        Specify a custom readonly bind mount.

        Readonly, recursive bind mounts aren't currently supported on Linux so
        this has to be a standalone option for now. Once they are, support for
        them and other mount attributes will be added as an extension to the
        mount point argument syntax.
    """)


@argparser.bind_final_check
def _validate_args(parser, namespace):
    if not namespace.command:
        namespace.command = [os.getenv('SHELL', '/bin/sh'), '-i']

    if not hasattr(namespace, 'mountpoints'):
        namespace.mountpoints = None

    if namespace.no_mounts:
        Chroot.default_mounts = {}


@argparser.bind_main_func
def main(options, out, err):
    try:
        with Chroot(options.path, mountpoints=options.mountpoints,
                    hostname=options.hostname, skip_chdir=options.skip_chdir) as c:
            subprocess.run(options.command)
    except FileNotFoundError as e:
        cmd = options.command[0]
        argparser.error(f'failed to run command {cmd!r}: {e}', status=1)
    except ChrootError as e:
        argparser.error(str(e), status=1)

    return c.exit_status

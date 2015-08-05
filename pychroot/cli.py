"""an extended chroot equivalent"""

from __future__ import unicode_literals

import argparse
import errno
from functools import partial
import os
import sys

from pychroot.base import Chroot
from pychroot.exceptions import ChrootError

from snakeoil.version import get_version


def bindmount(s, recursive=False, readonly=False):
    opts = {'recursive': recursive, 'readonly': readonly}
    return {s: opts}


class mountpoints(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, 'mountpoints', False):
            namespace.mountpoints = {}
        namespace.mountpoints.update(values)


argparser = argparse.ArgumentParser(
    description=__doc__.split('\n', 1)[0])
argparser.add_argument(
    '--version', action='version', version=get_version('pychroot', __file__))
argparser.add_argument('path', help='path to newroot')
argparser.add_argument(
    'command', nargs=argparse.REMAINDER, help='optional command to run')
argparser.add_argument(
    '--hostname', type=str, help='specify the chroot hostname')
argparser.add_argument(
    '--skip-chdir', action='store_true',
    help="do not change working directory to '/'")
argparser.add_argument(
    '-B', '--bind', type=bindmount, action=mountpoints,
    metavar='SRC[:DEST]', help='specify custom bind mount')
argparser.add_argument(
    '-R', '--rbind', type=partial(bindmount, recursive=True),
    action=mountpoints, metavar='SRC[:DEST]',
    help='specify custom recursive bind mount')

# Readonly support and similar things should be made into mount arg
# attributes once readonly, recursive bind mounts are supported on Linux.
argparser.add_argument(
    '--ro', '--readonly', type=partial(bindmount, readonly=True),
    action=mountpoints, metavar='SRC[:DEST]',
    help='specify custom readonly bind mount')


def parse_args(args):
    opts = argparser.parse_args(args)

    if not opts.command:
        opts.command = [os.getenv('SHELL', '/bin/sh'), '-i']

    if not hasattr(opts, 'mountpoints'):
        opts.mountpoints = None

    return opts


def main(args=None):
    args = args if args is not None else sys.argv[1:]
    opts = parse_args(args)

    try:
        with Chroot(opts.path, mountpoints=opts.mountpoints,
                    hostname=opts.hostname, skip_chdir=opts.skip_chdir):
            os.execvp(opts.command[0], opts.command)
    except EnvironmentError as e:
        if (e.errno == errno.ENOENT):
            raise SystemExit(
                "{}: failed to run command '{}': {}".format(
                os.path.basename(sys.argv[0]), opts.command[0], e.strerror))
        raise
    except ChrootError as e:
        raise SystemExit('{}: {}'.format(os.path.basename(sys.argv[0]), str(e)))

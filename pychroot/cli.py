import argparse
import errno
from functools import partial
import os
import sys

from pychroot.base import Chroot
from pychroot.exceptions import ChrootError


def bindmount(s, recursive=False, readonly=False):
    opts = {'recursive': recursive, 'readonly': readonly}
    return {s: opts}


class mountpoints(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, 'mountpoints', False):
            namespace.mountpoints = {}
        namespace.mountpoints.update(values)


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='A chroot(1) clone with extended functionality.')
    parser.add_argument('path', help='path to newroot')
    parser.add_argument(
        'command', nargs=argparse.REMAINDER, help='optional command to run')
    parser.add_argument(
        '-B', '--bind', type=bindmount, action=mountpoints,
        metavar='SRC[:DEST]', help='specify custom bind mount')
    parser.add_argument(
        '-R', '--rbind', type=partial(bindmount, recursive=True),
        action=mountpoints, metavar='SRC[:DEST]',
        help='specify custom recursive bind mount')

    # Readonly support and similar things should be made into mount arg
    # attributes once readonly, recursive bind mounts are supported on Linux.
    parser.add_argument(
        '--ro', '--readonly', type=partial(bindmount, readonly=True),
        action=mountpoints, metavar='SRC[:DEST]',
        help='specify custom readonly bind mount')

    opts = parser.parse_args(args)

    if not opts.command:
        opts.command = [os.getenv('SHELL', '/bin/sh'), '-i']

    return opts


def main(args=None):
    args = args if args is not None else sys.argv[1:]
    opts = parse_args(args)

    try:
        with Chroot(opts.path, mountpoints=getattr(opts, 'mountpoints', None)):
            os.execvp(opts.command[0], opts.command)
    except EnvironmentError as e:
        if (e.errno == errno.ENOENT):
            raise SystemExit(
                "{}: failed to run command '{}': {}".format(
                os.path.basename(sys.argv[0]), opts.command[0], e.strerror))
        raise
    except ChrootError as e:
        raise SystemExit('{}: {}'.format(os.path.basename(sys.argv[0]), str(e)))

import argparse
from functools import partial
import subprocess

from chroot import Chroot
from chroot.exceptions import ChrootError, ChrootMountError


def bindmount(s, recursive=False, readonly=False):
    opts = {'recursive': recursive, 'readonly': readonly}
    return {s: opts}


class mountpoints(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, 'mountpoints', False):
            namespace.mountpoints = {}
        namespace.mountpoints.update(values)


def main():
    parser = argparse.ArgumentParser(description='A simple chroot(1) workalike')
    parser.add_argument('path', help='path to newroot')
    parser.add_argument('command', nargs='*', help='optional command to run')
    parser.add_argument(
        '-B', '--bind', type=bindmount, action=mountpoints, metavar='SRC[:DEST]',
        help='specify custom bind mount')
    parser.add_argument(
        '-R', '--rbind', type=partial(bindmount, recursive=True),
        action=mountpoints, metavar='SRC[:DEST]',
        help='specify custom recursive bind mount')
    parser.add_argument(
        '--ro', '--readonly', type=partial(bindmount, readonly=True),
        action=mountpoints, metavar='SRC[:DEST]',
        help='specify custom readonly bind mount')
    args = parser.parse_args()

    command = ' '.join(args.command) if args.command else '/bin/sh -i'
    try:
        with Chroot(args.path, mountpoints=args.mountpoints):
            subprocess.call(command, shell=True)
    except (ChrootError, ChrootMountError, KeyboardInterrupt) as e:
        raise SystemExit(e)

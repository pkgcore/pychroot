import argparse
import errno
from functools import partial
import os
import sys

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


def parse_args(args):
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

    # Readonly support and similar things should be made into mount arg
    # attributes once readonly, recursive bind mounts are supported on Linux.
    parser.add_argument(
        '--ro', '--readonly', type=partial(bindmount, readonly=True),
        action=mountpoints, metavar='SRC[:DEST]',
        help='specify custom readonly bind mount')

    opts = parser.parse_args(args)

    if opts.command:
        command = ' '.join(opts.command)
    else:
        command = '%s -i' % os.environ.get('SHELL', '/bin/sh')
    command = command.split()

    opts.binary = command[0]
    # execv requires a nonempty second argument
    opts.binary_args = command[1:] if command[1:] else ['']

    del opts.command
    return opts


def main(args=None):
    args = args if args is not None else sys.argv[1:]
    opts = parse_args(args)

    try:
        with Chroot(opts.path, mountpoints=getattr(opts, 'mountpoints', None)):
            os.execvp(opts.binary, opts.binary_args)
    except EnvironmentError as e:
        if (e.errno == errno.ENOENT):
            raise SystemExit(
                "%s: failed to run command '%s': %s" %
                (os.path.basename(sys.argv[0]), opts.binary, e.strerror))
        raise
    except (ChrootError, ChrootMountError, KeyboardInterrupt) as e:
        raise SystemExit(e)

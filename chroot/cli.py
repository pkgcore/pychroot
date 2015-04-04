import argparse
import subprocess

from chroot import Chroot


def main():
    parser = argparse.ArgumentParser(description='A simple chroot(1) workalike')
    parser.add_argument('path', help='path to newroot')
    parser.add_argument('command', nargs='*', help='optional command to run')
    args = parser.parse_args()

    command = ' '.join(args.command) if args.command else '/bin/sh -i'
    with Chroot(args.path):
        subprocess.call(command, shell=True)

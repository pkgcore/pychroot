#!/usr/bin/env python

from importlib import import_module
import os
import sys


def main(script_name, args=None):
    args = args if args is not None else sys.argv[1:]
    try:
        script_module = '.'.join(
            os.path.realpath(__file__).split('/')[-3:-1] +
            [script_name.replace('-', '_')])
        script = import_module(script_module)
    except ImportError as e:
        sys.stderr.write('Failed importing: %s!\n' % str(e))
        sys.stderr.write(
            'Verify that snakeoil is properly installed '
            'and/or PYTHONPATH is set correctly for python %s.\n' %
            ('.'.join(map(str, sys.version_info[:3])),))
        if '--debug' in args:
            raise
        sys.stderr.write('Add --debug to the commandline for a traceback.\n')
        sys.exit(1)

    script.main(args)


if __name__ == '__main__':
    # we're in a git repo or tarball so add the base dir to the system path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main(os.path.basename(__file__))

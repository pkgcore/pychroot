# Copyright 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import errno
import os
import unittest

from chroot import namespaces


def test_setns():
    """Simple functionality test."""
    NS_PATH = '/proc/self/ns/mnt'
    if not os.path.exists(NS_PATH):
        raise unittest.SkipTest('kernel too old (missing %s)' % NS_PATH)

    with open(NS_PATH) as f:
        try:
            namespaces.setns(f.fileno(), 0)
        except OSError as e:
            if e.errno != errno.EPERM:
                # Running as non-root will fail, so ignore it.  We ran most
                # of the code in the process which is all we really wanted.
                raise


def test_unshare():
    """Simple functionality test."""
    try:
        namespaces.unshare(namespaces.CLONE_NEWNS)
    except OSError as e:
        if e.errno != errno.EPERM:
            # Running as non-root will fail, so ignore it.  We ran most
            # of the code in the process which is all we really wanted.
            raise

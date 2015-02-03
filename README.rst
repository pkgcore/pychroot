|test| |coverage|

========
pychroot
========

pychroot is a python library that simplifies chroot handling. Specifically, it
provides the **Chroot** context manager that allows for more pythonic methods
for running code in or controlling access to chroots.

Usage
=====

In its simplest form, pychroot can be used like the following::

    from chroot import Chroot

    with Chroot('/path/to/chroot'):
        code that will be run
        inside the chroot

By default, this will bind mount the host's /dev, /proc, and /sys filesystems
into the chroot as well as the /etc/resolv.conf file (so DNS resolution works
as expected in the chroot).

To customize that, **Chroot** accepts a *mountpoints* parameter that is a
dictionary of mappings to be merged with the defaults. Otherwise, it is also
possible to override the default mountpoints. See the documentation for more
details.

Namespaces are used by the context manager to segregate the chroot instance
from the host system. By default, new mount, UTS, IPC, and pid namespaces are
used. This allows for simplified handling of the teardown phase for the chroot
environments.

Requirements
============

Python versions 2.7, 3.3, 3.4 are supported. Note however, that the library is
quite Linux specific mainly due to the use of namespaces which requires kernel
support as well.

Issues
======

Please create an issue in the `issue tracker`_.

Tests
=====

Tests are handled via pytest, run via::

    py.test

which is also integrated into setup.py, run via::

    python setup.py test

A tox config is also provided so it's possible to run tests for all supported
versions of python by just calling *tox* in the git repo's root directory.

Installing
==========

via pip::

    pip install pychroot

manually::

    python setup.py install


.. _`issue tracker`: https://github.com/pkgcore/pychroot/issues

.. |test| image:: https://travis-ci.org/pkgcore/pychroot.svg?branch=master
    :target: https://travis-ci.org/pkgcore/pychroot

.. |coverage| image:: https://coveralls.io/repos/pkgcore/pychroot/badge.png?branch=master
    :target: https://coveralls.io/r/pkgcore/pychroot?branch=master

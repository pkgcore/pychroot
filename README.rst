|pypi| |test| |coverage|

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

A simple chroot(1) utility is installed as well as **pychroot**. It allows for
extended capabilities in terms of specifying custom bind mounts to perform, for example::

    sudo pychroot -B /home/user1 ~/chroot

will bind mount user1's home directory into the same location inside the chroot
directory in addition to the standard bind mounts listed previously. See
pychroot's help output for more options.

Notes
=====

Namespaces are used by the context manager to segregate the chroot instance
from the host system. By default, new mount, UTS, IPC, and pid namespaces are
used. This allows for simplified handling of the teardown phase for the chroot
environments.

One quirk of note is that currently local variables are not propagated back
from the chroot context to the main context due to the usage of separate
processes running the contexts. This means that something similar to the
following won't work::

    from chroot import Chroot

    with Chroot('/path/to/chroot'):
        a = 42
    print(a)

In this case, a NameError exception will be raised unless *a* was previously
defined. This will probably be fixed to some extent in a future release.

Requirements
============

Python versions 2.7, 3.3, 3.4 are supported. Note however, that pychroot is
quite Linux specific due to the use of namespaces via the `snakeoil`_ library
which also require proper kernel support.

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
versions of python by just calling *tox* in the project's root directory. Also,
note that mock_ is required for tests if you're using anything less than python
3.3.

Installing
==========

via pip::

    pip install pychroot

manually::

    python setup.py install


.. _`issue tracker`: https://github.com/pkgcore/pychroot/issues
.. _`snakeoil`: https://github.com/pkgcore/snakeoil
.. _mock: https://pypi.python.org/pypi/mock

.. |pypi| image:: https://img.shields.io/pypi/v/pychroot.svg
    :target: https://pypi.python.org/pypi/pychroot
.. |test| image:: https://travis-ci.org/pkgcore/pychroot.svg?branch=master
    :target: https://travis-ci.org/pkgcore/pychroot
.. |coverage| image:: https://coveralls.io/repos/pkgcore/pychroot/badge.png?branch=master
    :target: https://coveralls.io/r/pkgcore/pychroot?branch=master

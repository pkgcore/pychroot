|pypi| |test| |coverage|

========
pychroot
========

pychroot is a python library and cli tool that simplify chroot handling.
Specifically, the library provides a **Chroot** context manager that enables
more pythonic methods for running code in chroots while the **pychroot**
utility works much like an extended chroot command in the terminal.

Usage
=====

In its simplest form, the library can be used similar to the following::

    from pychroot import Chroot

    with Chroot('/path/to/chroot'):
        code that will be run
        inside the chroot

By default, this will bind mount the host's /dev, /proc, and /sys filesystems
into the chroot as well as the /etc/resolv.conf file (so DNS resolution works
as expected in the chroot).

A simple chroot equivalent is also installed as **pychroot**. It can be used in
a similar fashion to chroot; however, it also performs the bind mounts
previously mentioned so the environment is usable. In addition, pychroot
supports specifying custom bind mounts, for example::

    pychroot -R /home/user ~/chroot

will recursively bind mount the user's home directory at the same location
inside the chroot directory in addition to the standard bind mounts. See
pychroot's help output for more options.

When running on a system with a recent kernel (Linux 3.8 and on) and user
namespaces enabled pychroot can be run by a regular user. Currently
pychroot just maps the current user to root in the chroot environment. This
means that recursively chown-ing the chroot directory to the user running
pychroot should essentially allow that user to act as root in the pychroot
environment.

Implementation details
======================

Namespaces are used by the context manager to isolate the chroot instance from
the host system and to simplify the teardown phase for the environments. By
default, new mount, UTS, IPC, and pid namespaces are used.  In addition, if
running as non-root, both user and network namespaces will be enabled as well
so that the chrooting and mounting process will work without elevated
permissions.

One quirk of note is that currently local variables are not propagated back
from the chroot context to the main context due to the usage of separate
processes running the contexts. This means that something similar to the
following won't work::

    from pychroot import Chroot

    with Chroot('/path/to/chroot'):
        answer = 42
    print(answer)

In this case, a NameError exception will be raised unless the variable *answer*
was previously defined. This will probably be fixed to some extent in a future
release.

Requirements
============

pychroot is quite Linux specific due to the use of namespaces via the
`snakeoil`_ library which also require proper kernel support. Specifically, the
following kernel config options are required to be enabled for full namespace
support::

    CONFIG_NAMESPACES=y
    CONFIG_UTS_NS=y
    CONFIG_IPC_NS=y
    CONFIG_USER_NS=y
    CONFIG_PID_NS=y
    CONFIG_NET_NS=y

Installing
==========

In a virtualenv or elsewhere via pip::

    pip install pychroot

From the repo manually::

    python setup.py install

Bugs
====

Please create an issue in the `issue tracker`_.

Tests
=====

Tests are handled via pytest, run via::

    py.test

which is also integrated into setup.py, run via::

    python setup.py test

Also, tests for all supported python versions can be run together or
individually via::

    tox

Note that mock_ is required for tests when using python-2.7.


.. _`issue tracker`: https://github.com/pkgcore/pychroot/issues
.. _`snakeoil`: https://github.com/pkgcore/snakeoil
.. _mock: https://pypi.python.org/pypi/mock

.. |pypi| image:: https://img.shields.io/pypi/v/pychroot.svg
    :target: https://pypi.python.org/pypi/pychroot
.. |test| image:: https://travis-ci.org/pkgcore/pychroot.svg?branch=master
    :target: https://travis-ci.org/pkgcore/pychroot
.. |coverage| image:: https://coveralls.io/repos/pkgcore/pychroot/badge.png?branch=master
    :target: https://coveralls.io/r/pkgcore/pychroot?branch=master

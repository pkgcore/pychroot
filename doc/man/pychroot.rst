========
pychroot
========

.. include:: ../generated/pychroot/main_synopsis.rst

Description
===========

pychroot is an extended **chroot(1)** equivalent that also provides support for
automatically handling bind mounts. By default, the proc and sysfs filesystems
are mounted to their respective /proc and /sys locations inside the chroot as
well as bind mounting /dev and /etc/resolv.conf from the host system.

In addition to the defaults, the user is able to specify custom bind mounts.
For example, the following command will recursively bind mount the user's home
directory at the same location inside the chroot directory::

    pychroot -R /home/user ~/chroot

This allows a user to easily set up a custom chroot environment without having
to resort to scripted mount handling or other methods.

.. include:: ../generated/pychroot/main_options.rst

Example Usage
=============

Pass through the host system's ssh agent in order to support regular ssh auth
for a specific user in the chroot::

    pychroot -R /home/user --ro $SSH_AUTH_SOCK --ro /etc/passwd --ro /etc/shadow /path/to/chroot /bin/bash

Use the chroot environment while retaining access to the host file system::

    pychroot --skip-chdir /path/to/chroot /bin/bash

Set the chroot environment hostname to 'chroot' and the domain to 'foo.org'::

    pychroot --hostname chroot.foo.org /path/to/chroot /bin/bash

Reporting Bugs
==============

Please submit an issue via github:

https://github.com/pkgcore/pychroot/issues

You can also stop by #pkgcore on freenode.

See Also
========

chroot(1)

========
pychroot
========

.. include:: ../generated/pychroot/_synopsis.rst
.. include:: ../generated/pychroot/_description.rst
.. include:: ../generated/pychroot/_options.rst

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

See Also
========

chroot(1)

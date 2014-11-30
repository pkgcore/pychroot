|test| |coverage|

========
pychroot
========

pychroot is a python library that simplifies chroot handling. Specifically, it
provides the **Chroot** context manager that allows for more pythonic methods
for running code in or controlling access to chroots.

Issues
======

Please create an issue in the `issue tracker`_.

Tests
=====

Tests are handled via pytest, run via::

    py.test

which is also integrated into setup.py, run via::

    python setup.py test

Installing
==========

via pip::

    pip install pychroot

manually::

    python setup.py install


.. _`issue tracker`: https://github.com/radhermit/pychroot/issues

.. |test| image:: https://travis-ci.org/radhermit/pychroot.svg?branch=master
    :target: https://travis-ci.org/radhermit/pychroot

.. |coverage| image:: https://coveralls.io/repos/radhermit/pychroot/badge.png?branch=master
    :target: https://coveralls.io/r/radhermit/pychroot?branch=master

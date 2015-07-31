Release Notes
=============

pychroot 0.9.12 (2015-0?-??)
----------------------------

- Use $SHELL from the environment for the pychroot script to mirror chroot's
  behavior.

- Move WithParentSkip, the main parent/child execution splitting context
  manager allowing this all to work, to snakeoil.contextlib and rename it
  SplitExec. It was moved in order to develop other context managers around it
  in snakeoil and elsewhere more easily.

- Fix additional argument parsing for the pychroot script. Now commands like::

    pychroot ~/chroot /bin/bash -c "ls -R /"

  will work as expected (i.e. how they normally work with chroot).

- Allow mount propagation from the host mount namespace to the chroot's but not
  vice versa. Previously systems that set the rootfs mount as shared, e.g.
  running something like::

    mount --make-rshared /

  would leak mounts from the chroot mount namespace back into the host's
  namespace. Now the chroot mount namespace is recursively slaved from the
  host's so mount events will propagate down from host to chroot, but not back
  up from chroot to host.

pychroot 0.9.11 (2015-07-05)
----------------------------

- Fix pychroot script when no custom mountpoints as specified.

pychroot 0.9.10 (2015-04-09)
----------------------------

- Add support for custom bind mounts to the pychroot script. Now users are able
  to do things like::

    pychroot -R /home/user ~/chroot

  which will recursively bind mount their home directory into the chroot in
  addition to the standard set of bind mounts.

- Use "source[:dest]" as keys for mountpoints. This enables support for
  mounting the same source onto multiple destinations. For example, with
  pychroot it's now possible to run::

    pychroot -B tmpfs:/dev/shm -B tmpfs:/tmp

pychroot 0.9.9 (2015-04-03)
---------------------------

- Install chroot(1) workalike as pychroot. This allows users to be lazier when
  doing basic chrooting since pychroot handles mounting and unmounting standard
  bind mounts automatically.

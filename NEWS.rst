Release Notes
=============

pychroot 0.10.3 (2020-12-22)
----------------------------

- Fix build with newer versions of snakeoil.

pychroot 0.10.2 (2020-10-25)
----------------------------

- Add py3.9 support.

- Fix pychroot script hang on >=py3.7 (#30).

pychroot 0.10.1 (2019-11-30)
----------------------------

- Add py3.8 support.

pychroot 0.10.0 (2019-08-23)
----------------------------

- Minimum supported python version is now python3.6 (python2 support dropped).

- Fix handling of environment variable mounts to nonexistent paths.

pychroot 0.9.18 (2017-10-04)
----------------------------

- Return the exit status of the child process instead of 0 for the pychroot
  script. This makes pychroot more compatible with chroot's behavior.

- Run clean up before exit after receiving SIGINT/SIGTERM, previously stub
  files/directories that were created for bind mounts weren't properly cleaned
  up in the chroot after the parent process received these signals and exited.

pychroot 0.9.17 (2017-09-21)
----------------------------

- Handle single file bind mount creation failures.

pychroot 0.9.16 (2016-10-31)
----------------------------

- Don't try to generate new version files if they already exist (fixes another
  pip install issue).

- Drop py3.3 support.

pychroot 0.9.15 (2016-05-29)
----------------------------

- Fix new installs using pip.

pychroot 0.9.14 (2016-05-28)
----------------------------

- Move to generic scripts and docs framework used by pkgcore.

pychroot 0.9.13 (2015-12-13)
----------------------------

- Add --no-mounts option to disable the default mounts for the command line
  tool. This makes pychroot act similar to chroot.

- Make pychroot pip-installable without requiring wnakeoil to be manually
  installed first.

- Add lots of additional content to the pychroot utility man page.

pychroot 0.9.12 (2015-08-10)
----------------------------

- The main module was renamed from chroot to pychroot mostly for consistency to
  match the project name and cli tool installed alongside it.

- Add a man page for the pychroot cli tool.

- Add user namespace support so you can chroot as a regular user. Note that
  this also requires using a network namespace for which we only setup a
  loopback interface (if iproute2 is installed in the chroot) so external
  network access won't work by default in this situation.

- Add an option to skip changing to the newroot directory after chrooting. This
  is similar to the option for chroot(1) but also allows skipping the directory
  change when the new root isn't '/'. In other words, you can use a chroot
  environment against the host's rootfs.

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

- Add support for setting the chroot's host and domain names for all versions
  of python. Previously we only supported setting the hostname for py33 and up.
  To set the domain name, pass an FQDN instead of a singular hostname. This
  also adds a "--hostname" option to the pychroot script that enables the same
  support for it.

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

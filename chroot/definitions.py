DEFAULT_MOUNTS = {
    '/dev': {
        'recursive': True,
        'readonly': True,
    },
    '/proc': {},
    '/sys': {},
    '/config': {
        'optional': True,
    },
    '/debug': {
        'optional': True,
    },
    '/etc/resolv.conf': {},
}

# vim:et:ts=4:sw=4:tw=120:sts=4:ai:

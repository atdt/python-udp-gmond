#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Python Gmond Module for UDP

    :copyright: (c) 2012 Wikimedia Foundation
    :author: Ori Livneh <ori@wikimedia.org>
    :license: GPL
"""
from __future__ import print_function

import ast
import functools
import time


defaults = {
    "slope"      : "positive",
    "time_max"   : 60,
    "format"     : "%d",
    "value_type" : "double",
    "groups"     : "udp",
    "units"      : "packets"
}


udp_fields = {
    "InDatagrams"  : "packets received",
    "NoPorts"      : "packets to unknown port received",
    "InErrors"     : "packet receive errors",
    "OutDatagrams" : "packets sent"
}


def throttle(seconds):
    """
    Decorator; when decorated function is called, caches its return value and
    sets a cooldown timer. Subsequent calls to the decorated function while the
    cooldown timer is in effect receive the cached value.
    """
    last = dict(value=None, expires=0)
    def outer(f):
        @functools.wraps(f)
        def inner():
            now = time.time()
            if now > last['expires']:
                last['value'] = f()
                last['expires'] = now + seconds
            return last['value']
        return inner
    return outer


@throttle(seconds=10)
def netstats():
    """Parse /proc/net/snmp like netstat does"""
    with open('/proc/net/snmp', 'rt') as snmp:
        raw = {}
        for line in snmp:
            key, vals = line.split(':', 1)
            key = key.lower()
            vals = vals.strip().split()
            raw.setdefault(key, []).append(vals)
    return dict((k, dict(zip(*vs))) for (k, vs) in raw.items())


def metric_handler(name):
    """Get value of particular metric; part of Gmond interface"""
    return ast.literal_eval(netstats()['udp'][name])


def metric_init(params):
    """Initialize; part of Gmond interface"""
    descriptors = []
    defaults['call_back'] = metric_handler
    for name, description in udp_fields.items():
        descriptor = dict(name=name, description=description)
        descriptor.update(defaults)
        descriptors.append(descriptor)
    return descriptors

def metric_cleanup():
    """Teardown; part of Gmond interface"""
    pass


if __name__ == '__main__':
    # When invoked as standalone script, run a self-test by querying each
    # metric descriptor and printing it out.
    for metric in metric_init({}):
        value = metric['call_back'](metric['name'])
        print(( "%s => " + metric['format'] ) % ( metric['name'], value ))

#!/usr/bin/env python

from cloudify import ctx

if __name__ == '__main__':
    ctx.instance.runtime_properties['KUBERNETES_MASTER'] = True

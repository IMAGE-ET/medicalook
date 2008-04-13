#!/usr/bin/env python
#
# medicalook.py: entry point of Medicalook
# author: Jesse Woo <jessewoo at gmail.com>
# license: GPL

import sys, os
import getopt

import common


def main():
    try:
        options, args = getopt.getopt(sys.argv[1:], 'hv',
                                      ['help', 'version'])
    except getopt.GetoptError:
        usage()
    for o, a in options:
        if o in ('-h', '--help'):
            usage(False)
        elif o in ('-v', '--version'):
            version()

    import main
    main.main()


def usage(err=True):
    if err:
        stream = sys.stderr
    else:
        stream = sys.stdout

    print >> stream, """Usage: %s [OPTIONS]
Valid OPTIONS:
-h, --help:    shows this message and exits
-v, --version: show version
""" % os.path.basename(sys.argv[0])
    sys.exit(err)


def version():
    print common.__version__


if __name__ == '__main__':
    main()

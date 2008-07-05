#!/usr/bin/env python
#
# common.py: global client configuration
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

import os

__version__ = '0.1'

if os.path.expanduser('~') != '~':
    confdir = os.path.expanduser('~/.medicalook')
    config_file = os.path.expanduser('~/.medicalook/config')
    if not os.path.exists(confdir):
        try: os.mkdir(confdir)
        except (IOError, OSError): pass # this is not fatal
else:
    confdir = os.path.dirname(sys.argv[0])
    config_file = os.path.join(confdir, 'config')

config = None # ConfigPaser instance used to load/store options

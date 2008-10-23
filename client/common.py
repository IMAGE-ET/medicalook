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
    file_dir = os.path.expanduser('~/.medicalook/data')
    if not os.path.exists(confdir):
        try: os.mkdir(confdir)
        except (IOError, OSError): pass # this is not fatal
    if not os.path.exists(file_dir):
        try: os.mkdir(file_dir)
        except (IOError, OSError): pass # this is not fatal
    if not os.path.exists(config_file):
        open(config_file, 'w').close()
else:
    confdir = os.path.dirname(sys.argv[0])
    config_file = os.path.join(confdir, 'config')
    file_dir = os.path.join(confdir, 'data')

# ConfigPaser instance used to load/store options
config = None

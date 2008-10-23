#!/usr/bin/env python
#
# common.py: global server configuration
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

import os

__version__ = '0.1'

if os.path.expanduser('~') != '~':
    confdir = os.path.expanduser('~/.medicalookd')
    config_file = os.path.expanduser('~/.medicalookd/config')
    if not os.path.exists(confdir):
        try: os.mkdir(confdir)
        except (IOError, OSError): pass # this is not fatal
else:
    confdir = os.path.dirname(sys.argv[0])
    config_file = os.path.join(confdir, 'config')

# ConfigPaser instance used to load/store options
config = None

# chunk size for file transfer
chunk_size = 2 ** 16

file_dir = '/home/jesse/tmp/dicom'

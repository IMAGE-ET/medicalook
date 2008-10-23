#!/usr/bin/env python
#
# medproto_client.py: client protocol for medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet import reactor, defer

import os
from zlib import crc32

import common
from metadata import columns


class MedicalookClientProtocol(LineReceiver):

    def __init__(self):
        self.filesize_remain = 0
        self.crc_src = 0
        self.crc = 0

    def _error(self, msg):
        line = '0#' + msg
        self.sendLine(line)

    def lineReceived(self, line):
        print "receive line", line
        response_type, line = line.split('#', 1)
        {'0': self._error_handler,
         '1': self._list_response_handler,
         '2': self._image_response_handler,
         '3': self._import_response_handler}[response_type](line)

    def _error_handler(self, line):
        print "error: %s" % line

    def _list_response_handler(self, line):
        fields = line.split('#')
        if len(fields) == 2:
            self.factory.list_total, self.factory.list_count = map(int, fields)
            self.factory.list_data = []
            if self.factory.list_count == 0:
                self.factory.deferred_list.callback(self.factory.list_data)
        else:
            fields = line.split('|')
            self.factory.list_data.append(fields)
            if len(self.factory.list_data) == self.factory.list_count:
                self.factory.deferred_list.callback(self.factory.list_data)

    def _image_response_handler(self, line):
        filename, filesize_remain, crc_src = line.split('|')
        filepath = os.path.join(common.file_dir, filename)
        self.filesize_remain = int(filesize_remain)
        self.crc_src = int(crc_src)
        self.filepath = filepath
        self.outfile = open(filepath, 'wb')
        self.setRawMode()

    def _import_response_handler(self, line):
        image_id = int(line)

    def rawDataReceived(self, data):
        self.filesize_remain -= len(data)
        self.crc = crc32(data, self.crc)
        self.outfile.write(data)
        if self.filesize_remain == 0:
            self.outfile.close()
            self.factory.deferred_image.callback(self.filepath)
            if self.crc == self.crc_src:
                self.crc = 0
            else:
                os.remove(self.filepath)
                self._error('crc dismatch')
            self.setLineMode()

    def connectionMade(self):
        LineReceiver.connectionMade(self)
        print "server connected"

    def connectionLost(self, reason):
        LineReceiver.connectionLost(self, reason)
        print "connection lost"

class MedicalookClientFactory(ClientFactory):

    protocol = MedicalookClientProtocol

    def __init__(self, main_frame):
        self.main_frame = main_frame
        self.connected = False

        self.list_total = 0
        self.list_count = 0
        self.list_data = []

        self.image_id = None

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        self.connected = False

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        self.connected = False
        msg = "Can not connect to %s." % common.host
        self.main_frame.show_error(msg)

    def buildProtocol(self, addr):
        print 'build client protocol'
        self.connected = True
        self.client_instance = self.protocol()
        self.client_instance.factory = self
        return self.client_instance

    def list_query(self, dic, limit, offset):
        if not self.connected:
            msg = "Medicalook is currenly disconnected."
            self.main_frame.show_error(msg)
            return None
        self.deferred_list = defer.Deferred()
        line = '1#'
        for item in columns:
            if (item in dic) and dic[item]:
                s = dic[item]
                line += '%s|' % s
            else:
                line += '*|'
        line = line[:-1] + '#%s#%s' % (limit, offset)
        print "line sent: ", line
        self.client_instance.sendLine(line)
        return self.deferred_list

    def image_query(self, image_id):
        if not self.connected:
            msg = "Medicalook is currenly disconnected."
            self.main_frame.show_error(msg)
            return None
        self.image_id = image_id
        self.deferred_image = defer.Deferred()
        line = '2#%s' % image_id
        print 'line sent: ', line
        self.client_instance.sendLine(str(line))
        return self.deferred_image

    def import_query(self, path):
        if not self.connected:
            msg = "Medicalook is currenly disconnected."
            self.main_frame.show_error(msg)
            return None
        f = open(path, 'rb')
        s = f.read()
        f.seek(0)
        filesize = len(s)
        crc = crc32(s)
        ext = os.path.splitext(path)[1][1:].lower()
        line = '3#%s|%s|%s' % (filesize, crc, ext)
        print "send line:", line
        self.client_instance.sendLine(str(line))
        self.client_instance.setRawMode()
        remain = s
        while remain:
            data = remain[:common.chunk_size]
            remain = remain[common.chunk_size:]
            self.client_instance.transport.write(data)
        f.close()
        self.client_instance.setLineMode()

#!/usr/bin/env python
#
# medproto.py: server protocol for medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet.defer import DeferredList

import os

import common
import db


def delete_colon(string):
    return string.replace(':', ' ')

class MedicalookServerProtocol(LineReceiver):
    """
    There are 4 types of communication between server(s) and
    client(c):

    0. Error:
         s --> c: 0#message
         or
         c --> s: 0#message

    1. List querying:
         c --> s: 1#*:John:m:*:*:*#limit#offset
         s --> c: 1#total#number of rows to transfer
         s --> c: 1#123231231:John:m:1934-2-3:head::MR
         s --> c: 1#234567899:John:m:1945-5-8:Spline:description:CT
         ...

    2. Image querying:
         c --> s: 2#123231231
         s ==> c: image file of id 123231231

    3. Import querying:
         c --> s: 3#the number of images to transfer
         c --> s: 3#filesize:crc
         c ==> s: image 1
         c --> s: 3#filesize:crc
         c ==> s: image 2
         ...
         s --> c: 3#assigned ids of the imported images seperated by
                  ':'

    '-->' denotes string mode, '==>' denotes rawdata mode.

    If any received message is of unknown format, send '0#message'
    """

    def __init__(self):
        self.current_import_file = None
        self.import_id_list = []
        self.import_remain = 0
        self.filesize_remain = 0
        self.crc_src = 0
        self.crc = 0

    def _error(self, msg):
        line = '0#' + msg
        self.sendLine(line)

    def lineReceived(self, line):
        query_type, line = line.split('#', 1)
        {'0': self._error_handler,
         '1': self._list_querying_handler,
         '2': self._image_querying_handler,
         '3': self._import_querying_handler}[query_type](line)

    def _error_handler(self, line):
        pass

    def _list_querying_handler(self, line):
        line, limit, offset = line.split('#')

        # convet the line to a list based on the delimeter ':'
        line.replace('\:', '|')
        query = map(lambda x: x.replace('|', ':'), line.split(':'))

        if len(query) != len(self.factory.header):
            self._error('list querying: format incorrect')
        else:
            # constuct response lines
            def send_lines(result):
                r_total, r_count, r_data  = result
                if r_total[0] + r_count[0] + r_data[0] < 3:
                    print "database query error"
                    return
                count_line = '1#%s#%s' % (r_total[1], r_count[1])
                self.sendLine(count_line)

                for row in r_data[1]:
                    line = ':'.join(map(delete_colon, row))
                    self.sendLine(line)

            # build SQL query
            where = ''
            for i, item in enumerate(query):
                if item != '*':
                    where += " %s = '%s' AND" % \
                    (self.factory.header[i], item)

            # get rid of the last ' AND'
            where = where[:-4]

            where_limit = where + \
                          ' LIMIT %s OFFSET %s' % (limit, offset)

            d_total = db.get_count_where(where)
            d_count = db.get_count_where(where_limit)
            d_data = db.get_all_where(where_limit)
            dl = DeferredList([d_total, d_count, d_data])
            dl.addCallback(send_lines)

    def _image_querying_handler(self, line):
        try:
            image_id = int(line)
        except ValueError:
            self._error('image querying: image id incorrect')
        else:
            def send_file(filename):
                filepath = os.path.join(common.file_dir, filename)
                try:
                    outfile = open(filepath, 'rb')
                except IOError:
                    print "no such file"
                    return

                def transfer_completed(lastsent):
                    outfile.close()

                sender = FileSender()
                sender.CHUNK_SIZE = 2 ** 16
                d = sender.beginFileTransfer(outfile, self.transport)
                d.addCallback(transfer_completed)

            where = "id = %s" % image_id
            d_filename = db.get_field_where('filename', where)
            d_filename.addCallback(send_file)

    def _import_querying_handler(self, line):
        fields = line.split(':')

        if len(fields) == 1:
            try:
                how_many = int(line)
            except ValueError:
                self._error('import querying: expect an integer')
                return
            else:
                self.import_remain = how_many
        else:
            try:
                filesize, self.crc_src = map(int, fields)
            except ValueError:
                self._error('count, filesize expect a integer')
                return

            if self.import_remain <= 0:
                self._error('import count exceeds total')
                return
            else:
                name = uuid.uuid4()
                path = os.path.join(common.file_dir, name)
                self.current_import_file = open(path, 'wb')
                self.current_import_name = name
                self.filesize_remain = filesize
                self.setRawMode()

    def _import_completed(self):
        # return a filename list to client
        pass

    def rawDataReceived(self, data):
        self.remain -= len(data)
        self.crc = crc32(data, self.crc)
        self.current_import_file.write(data)
        if self.filesize_remain == 0:
            self.import_remain -= 1
            self.current_import_file.close()
            if self.crc == self.crc_src:
                self.crc = 0
                import_th = FileImporter(self.current_import_name)
                import_th.start()
                import_th.join()
                # TODO: http://artfulcode.nfshost.com/files/multi-threading-in-python.html
            else:
                os.remove(os.path.join(common.file_dir,
                                       self.current_import_name))
                self._error('crc dismatch')
            self.setLineMode()
            if self.import_remain == 0:
                self._import_completed()

    def connectionMade(self):
        LineReceiver.connectionMade(self)
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        LineReceiver.connectionLost(self, reason)
        self.factory.clients.remove(self)


class MedicalookServerFactory(Factory):

    protocol = MedicalookServerProtocol

    def __init__(self, header):
        self.header = header
        self.clients = []

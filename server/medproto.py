#!/usr/bin/env python
#
# medproto.py: server protocol for medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.defer import DeferredList

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
         s --> c: 1#total#count to transfer
         s --> c: 123231231:John:m:1934-2-3:head::MR
         s --> c: 1#234567899:John:m:1945-5-8:Spline:description:CT
         ...

    2. Image querying:
         c --> s: 2#123231231
         s ==> c: image file of id 123231231

    3. Import querying:
         c --> s: 3#the number of images to transfer
         c ==> s: image 1
         c ==> s: image 2
         ...
         s --> c: 3#assigned ids of the imported images seperated by
                  ':'

    '-->' denotes string mode, '==>' denotes rawdata mode.

    If any received message is of unknown format, send '0#message'
    """

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
            where = where[:-4] # get rid of the last ' AND'
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
            where = "id = %s" % image_id
            #TODO: find the image and send the image to client

    def _import_querying_handler(self, line):
        try:
            how_many = int(line)
        except ValueError:
            self._error('import querying: expect an integer')
        else:
            pass
            #TODO: prepare to receive a series of images

    def rawDataReceived(self):
        self.setLineMode()

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)


class MedicalookServerFactory(Factory):

    protocol = MedicalookServerProtocol

    def __init__(self, header):
        self.header = header
        self.clients = []

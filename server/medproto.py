#!/usr/bin/env python
#
# medproto.py: server protocol for medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet.defer import DeferredList
from twisted.internet import threads

import os
import uuid
import shutil, glob
from zlib import crc32

import common
import db
import import_thread
from metadata import connector

class MedicalookServerProtocol(LineReceiver):
    """
    There are 4 types of communication between server(s) and
    client(c):

    0. Error:
         s --> c: 0#message
         or
         c --> s: 0#message

    1. List querying:
         c --> s: 1#*|John|m|*|*|*#limit#offset
         s --> c: 1#total|number of rows to transfer
         s --> c: 1#123231231|John|m|1934-2-3|head||MR
         s --> c: 1#234567899|John|m|1945-5-8|Spline|description|CT
         ...

    2. Image querying:
         c --> s: 2#123231231
         s --> c: 2#filename|filesize|crc
         s ==> c: image file of id 123231231

    3. Import querying:
         c --> s: 3#filesize|crc|ext
         c ==> s: image 1
         s --> c: 3#assigned id (currently not implemented)

    '-->' denotes string mode, '==>' denotes rawdata mode.

    If any received message is of unknown format, send '0#message'
    """

    def __init__(self):
        self.current_import_file = None
        self.import_id = None
        self.filesize_remain = 0
        self.crc_src = 0
        self.crc = 0
        self.rar = False

        self.excess_flag = False
        self.excess_no_linebreak_flag = False
        self.excess_no_linebreak_data = ''

    def _error(self, msg):
        line = '0#' + msg
        self.sendLine(line)

    def lineReceived(self, line):
        print "receive line:", line
        query_type, line = line.split('#', 1)
        {'0': self._error_handler,
         '1': self._list_querying_handler,
         '2': self._image_querying_handler,
         '3': self._import_querying_handler}[query_type](line)

    def _error_handler(self, line):
        print "error: %s" % line

    def _list_querying_handler(self, line):
        line, limit, offset = line.split('#')

        # convet the line to a list based on the delimeter '|'
        query = line.split('|')

        if len(query) != len(self.factory.columns):
            self._error('list querying: format incorrect')
        else:
            # constuct response lines
            def send_lines(result):
                r_total, r_count, r_data  = result
                if r_total[0] + r_count[0] + r_data[0] < 3:
                    print "database query error"
                    return
                count_line = '1#%s#%s' % (r_total[1][0][0], r_count[1][0][0])
                self.sendLine(count_line)

                for row in r_data[1]:
                    str_row = map(str, row)
                    line = '1#' + '|'.join(str_row)
                    self.sendLine(line)

            # build SQL query
            where = 'WHERE'
            for i, item in enumerate(query):
                if item != '*':
                    if self.factory.columns[i] == 'study_date':
                        dates = item.split('~')
                        if len(dates) == 2:
                            where += " (study_date BETWEEN \
                            DATE '%s' AND DATE '%s') AND" % tuple(dates)
                        elif len(dates) == 1:
                            where += " study_date = DATE '%s' AND" % item
                    elif self.factory.columns[i] == 'patient_dob':
                        year = " EXTRACT(YEAR FROM AGE(patient_dob))"
                        if '~' in item:
                            f, t = map(int, item.split('~'))
                            s = year + " BETWEEN %d and %d" % (f, t)
                        else:
                            s = year + " = %d" % int(item)
                        where += (s + ' AND')
                    else:
                        con = connector[self.factory.columns[i]]
                        where += " %s %s '%s' AND" % \
                                 (self.factory.columns[i], con, item)

            if where == 'WHERE':
                where = ''
            else:
                # get rid of the last ' AND'
                where = where[:-4]

            print "WHERE:", where
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
            def send_file(result):
                filename = result[0][0].strip()
                filepath = os.path.join(common.file_dir, filename)
                print "send file ", filepath
                try:
                    outfile = open(filepath, 'rb')
                except IOError:
                    print "no such file"
                    return
                else:
                    s = outfile.read()
                    outfile.seek(0)
                    filesize = len(s)
                    crc = crc32(s)
                    line = '2#%s|%s|%s' % (filename, filesize, crc)
                    self.sendLine(line)

                def transfer_completed(lastsent):
                    outfile.close()

                sender = FileSender()
                sender.CHUNK_SIZE = common.chunk_size
                d = sender.beginFileTransfer(outfile, self.transport)
                d.addCallback(transfer_completed)

            where = "WHERE id = %s" % image_id
            d_filename = db.get_field_where('filename', where)
            d_filename.addCallback(send_file)

    def _import_querying_handler(self, line):
        fields = line.split('|')
        try:
            filesize = int(fields[0])
            self.crc_src = int(fields[1])
            ext = fields[2]
        except ValueError:
            self._error('count, filesize expect a integer')
            return

        if (ext == 'rar'):
            self.rar = True
        else:
            self.rar = False
            if not (ext == 'dcm' or ext == 'DCM' or \
                    ext == 'acr' or ext == "ACR"):
                return

        name = uuid.uuid4().get_hex() + '.' + ext
        path = os.path.join(common.file_dir, name)
        self.current_import_file = open(path, 'wb')
        self.current_import_name = name
        self.filesize_remain = filesize
        print "import %s" % name
        self.setRawMode()

    def _import_completed(self):
        line = '3#%d' % self.import_id
        self.sendLine(str(line))

    def _append_id(self, res):
        pass

    def _parse(self, filename):
        d = threads.deferToThread(import_thread.parse_file, filename)
        d.addCallback(import_thread.insert_data)

    def _parse_many(self, a):
        # remove rar file
        os.chdir(common.file_dir)
        files = glob.glob('*.rar')
        for f in files:
            os.remove(f)

        # parse each dicom file
        tmp_dir = os.path.join(common.file_dir, 'tmp')
        #files = glob.glob('%s/*.DCM' % tmp_dir)
        files = glob.glob('%s/*' % tmp_dir)
        for f in files:
            name = uuid.uuid4().get_hex() + '.dcm'
            shutil.move(f, os.path.join(common.file_dir, name))
            self._parse(name)

    def _extract(self, filename):
        try:
            path = os.path.join(common.file_dir, filename)
            tmp_dir = os.path.join(common.file_dir, 'tmp')
            if not os.path.exists(tmp_dir):
                try: os.mkdir(tmp_dir)
                except (IOError, OSError): pass # this is not fatal
            os.chdir(tmp_dir)
            command = "rar e %s" % path
            d = threads.deferToThread(os.system, command)
            d.addCallback(self._parse_many)
        except:
            return

    def rawDataReceived(self, data):
        # this function contains a huge bug, fix soon
        if self.excess_no_linebreak_flag:
            data = self.excess_no_linebreak_data + data
            self.excess_no_linebreak_flag = False

        if (len(data) - len(self.excess_no_linebreak_data)) > \
               self.filesize_remain:
            self.excess_flag = True
            excess = data[self.filesize_remain:]
            data = data[:self.filesize_remain]
            parts = excess.split('\r\n', 1)
            if len(parts) == 2:
                pre, post = parts
                excess_line = pre
                excess_data = post
            else:
                self.excess_no_linebreak_flag = True
                self.excess_no_likebreak_data = excess

        self.filesize_remain -= len(data)
        self.crc = crc32(data, self.crc)
        self.current_import_file.write(data)
        if self.filesize_remain <= 0:
            print "%s import ok" % self.current_import_name
            self.current_import_file.close()
            if self.crc == self.crc_src:
                self.crc = 0
                if self.rar:
                    self._extract(self.current_import_name)
                else:
                    self._parse(self.current_import_name)
            else:
                self.import_total_files -= 1
                os.remove(os.path.join(common.file_dir,
                                       self.current_import_name))
                self._error('crc dismatch')
                # TODO: resend request
            self.setLineMode()

            if self.excess_flag and not self.excess_no_linebreak_flag:
                self.excess_flag = False
                if excess_line:
                    self.lineReceived(excess_line)
                if excess_data:
                    self.rawDataReceived(excess_data)


    def connectionMade(self):
        print "a new client connected ..."
        LineReceiver.connectionMade(self)
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print "a client disconnected ..."
        LineReceiver.connectionLost(self, reason)
        self.factory.clients.remove(self)


class MedicalookServerFactory(Factory):

    protocol = MedicalookServerProtocol

    def __init__(self, columns):
        self.columns = columns
        self.clients = []

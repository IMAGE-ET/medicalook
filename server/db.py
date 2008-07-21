#!/usr/bin/env python
#
# db.py: database module of medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

from twisted.enterprise import adbapi

try:
    dbpool = adbapi.ConnectionPool('pyPgSQL.PgSQL',
                                   database='medicalook',
                                   host='localhost',
                                   user='medicalook',
                                   password='medicalook')
except:
    print "unable to connect to database"


def get_all():
    return dbpool.runQuery("SELECT * FROM images")

def get_count():
    return dbpool.runQuery("SELECT count(*) FROM images")

def get_all_where(where):
    print "SELECT * FROM images %s" % where
    return dbpool.runQuery("SELECT * FROM images %s" % where)

def get_count_where(where):
    print "SELECT count(*) FROM images %s" % where
    return dbpool.runQuery("SELECT count(*) FROM images %s" % where)

def get_field_where(field, where):
    return dbpool.runQuery("SELECT %s FROM images %s" % (field, where))

def run_op(sql):
    return dbpool.runOperation(sql)

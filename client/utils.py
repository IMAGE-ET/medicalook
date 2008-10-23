#!/usr/bin/env python
#
# utils.py: miscellaneous functions
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

import os, datetime
import wx


def locate(root=os.curdir):
    paths = []
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in files:
            paths.append(os.path.join(path, filename))
    return paths

def pydate2wxdate(date):
    assert isinstance(date, (datetime.datetime, datetime.date))
    tt = date.timetuple()
    dmy = (tt[2], tt[1]-1, tt[0])
    return wx.DateTimeFromDMY(*dmy)

def wxdate2pydate(date):
    assert isinstance(date, wx.DateTime)
    if date.IsValid():
        ymd = map(int, date.FormatISODate().split('-'))
        return datetime.date(*ymd)
    else:
        return None

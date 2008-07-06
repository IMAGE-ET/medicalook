#!/usr/bin/env python
#
# virtual_listctrl.py: virtual list control of the browser frame
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL


import wx
import sys, glob, random

import server.db
from server.metadata import columns


class DataSource:
    """
    A simple data source class that just uses our sample data items.
    A real data source class would manage fetching items from a
    database or similar.
    """
    def __init__(self):
        self.rows = None
        self.refresh()

    def refresh(self):
        server.db.get_all().addCallback(self._update)

    def _update(self, results):
        self.rows = results
        print len(self.rows)

    def get_column_headers(self):
        return columns

    def get_count(self):
        return server.db.get_count()

    def get_item(self, index):
        if self.rows:
            return self.rows[index]
        else:
            return None

    def update_cache(self, start, end):
        pass


class VirtualListCtrl(wx.ListCtrl):
    """
    A generic virtual listctrl that fetches data from a data source.
    """
    def __init__(self, parent, datasource):

        wx.ListCtrl.__init__(self, parent, -1,
                             style=wx.LC_REPORT|wx.LC_SINGLE_SEL \
                             |wx.LC_VIRTUAL|wx.SUNKEN_BORDER)
        self.data_source = datasource
        self.Bind(wx.EVT_LIST_CACHE_HINT, self.DoCacheItems)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        self._set_count()
        columns = self.data_source.get_column_headers()
        for col, text in enumerate(columns):
            self.InsertColumn(col, text)

    def DoCacheItems(self, evt):
        self.data_source.update_cache(
            evt.GetCacheFrom(), evt.GetCacheTo())

    def OnGetItemText(self, item, col):
        data = self.data_source.get_item(item)
        if data:
            return str(data[col])

    def OnGetItemAttr(self, item):
        return None

    def OnGetItemImage(self, item):
        return -1

    def _on_item_selected(self, evt):
        item = evt.GetItem()
        print "Item selected:", item.GetColumn()

    def refresh(self):
        self.data_source.refresh()
        self._set_count()

    def _set_count(self):
        self.data_source.get_count().addCallback(self._set_item_count)

    def _set_item_count(self, result):
        self.SetItemCount(result[0][0])

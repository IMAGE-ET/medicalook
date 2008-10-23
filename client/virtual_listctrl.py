#!/usr/bin/env python
#
# virtual_listctrl.py: virtual list control of the browser frame
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL


import wx
import os, sys, glob, random, time

from twisted.internet import threads

import common
from metadata import headers


class DataSource:
    """
    A simple data source class that just uses our sample data items.
    A real data source class would manage fetching items from a
    database or similar.
    """
    def __init__(self):
        self.rows = []
        self.refresh()

    def refresh(self):
        pass

    def get_column_headers(self):
        return headers

    def get_count(self):
        return len(self.rows)

    def get_row(self, index):
        if self.rows and index <= (len(self.rows) - 1):
            return self.rows[index]
        else:
            return None

    def update_cache(self, start, end):
        pass

    def set_rows(self, rows):
        self.rows = rows

class VirtualListCtrl(wx.ListCtrl):
    """
    A generic virtual listctrl that fetches data from a data source.
    """
    def __init__(self, parent, datasource, client):

        wx.ListCtrl.__init__(self, parent, -1,
                             style=wx.LC_REPORT|wx.LC_SINGLE_SEL \
                             |wx.LC_VIRTUAL|wx.SUNKEN_BORDER)

        self.Bind(wx.EVT_LIST_CACHE_HINT, self._on_cache_items)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)

        self.main_frame = parent.GetParent()
        self.data_source = datasource
        self.client = client
        self.count = 0
        self.columns = self.data_source.get_column_headers()
        for col, text in enumerate(self.columns):
            self.InsertColumn(col, text)
            self.SetColumnWidth(col, 80)

    def resize_column(self):
        self.refresh()
        for col in range(len(self.columns)):
            self.SetColumnWidth(col, wx.LIST_AUTOSIZE)

    def OnGetItemText(self, row_idx, col):
        row = self.data_source.get_row(row_idx)
        if row:
            return str(row[col])

    def OnGetItemAttr(self, item):
        return None

    def OnGetItemImage(self, item):
        return -1

    def _on_cache_items(self, evt):
        self.data_source.update_cache(
            evt.GetCacheFrom(), evt.GetCacheTo())

    def _on_item_selected(self, evt):
        self.current_idx = evt.m_itemIndex
        image_id = self.GetItemText(self.current_idx)
        print "Item selected:", image_id

    def _on_item_activated(self, evt):
        self.current_idx = evt.m_itemIndex
        row = self.data_source.get_row(self.current_idx)
        image_id = self.GetItemText(self.current_idx)
        if not self.client.image_query(image_id):
            return
        if not common.viewer_path:
            self.main_frame.show_error("You haven't set a dicom viewer yet.")
            return
        filename = row[10].strip()
        filepath = os.path.join(common.file_dir, filename)
        d = threads.deferToThread(self._open_image, filepath)
        d.addCallback(self._open_image_complete)

    def _open_image(self, filepath):
        while not os.path.exists(filepath):
            print "checking:", filepath
            time.sleep(2)
        command = "%s %s" % (common.viewer_path, filepath)
        os.system(command)
        return filepath

    def _open_image_complete(self, filepath):
        print "image opened: ", filepath

    def refresh(self):
        self.data_source.refresh()
        self._set_count()

    def _set_count(self):
        self.count = self.data_source.get_count()
        self.SetItemCount(self.count)

#!/usr/bin/env python
#
# main.py: main module of Medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

import sys, os
import wx

from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor

import common
import server.db


class Medicalook(wx.App):
    def __init__(self):
        self.main_frame = None
        self.viewer = None
        self.viewer_frame = None
        wx.App.__init__(self, 0)

    def OnInit(self):
        #self.init_preferences()
        #self.viewer_frame = viewer.DicomViewerFrame(None, '')
        #self.viewer = viewer.DicomViewer()
        self.main_frame = MedicalookBrowser()
        self.SetTopWindow(self.main_frame)
        self.main_frame.Show()
        return True

    def init_preferences(self):
        import ConfigParser
        defaults = {
            'server': 'localhost',
            'port': '5213',
            }
        common.config = ConfigParser.ConfigParser(defaults)
        common.config.read(common.config_file)
        if not common.config.has_section('medicalook'):
            common.config.add_section('medicalook')
        common.server = common.config.get('medicalook', 'server')
        common.port = common.config.getint('medicalook', 'port')


class MedicalookBrowser(wx.Frame):
    def __init__(self, **kwds):
        wx.Frame.__init__(self, None, -1, 'medicalook')

        self._create_menubar()
        panel = wx.Panel(self, -1)
        panel_search = wx.Panel(panel, -1, size=(-1, 100),
                                style=wx.SUNKEN_BORDER)
        from virtual_listctrl import VirtualListCtrl, DataSource
        self.list = VirtualListCtrl(panel, DataSource())

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel_search, 0, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 10)
        sizer.Add(self.list, 1, wx.EXPAND|wx.ALL, 10)

        panel.SetSizer(sizer)
        self.Centre()
        self.Show(True)

    def _create_menubar(self):
        menubar = wx.MenuBar()
        for item in self._menu_data():
            menu_label = item[0]
            menu_item = item[1]
            menubar.Append(self._create_menu(menu_item), menu_label)
        self.SetMenuBar(menubar)

    def _create_menu(self, menu_item):
        menu = wx.Menu()
        for item in menu_item:
            if len(item) == 2:
                label = item[0]
                submenu = self._create_menu(item[1])
                menu.AppendMenu(wx.NewId(), label, submenu)
            else:
                self._create_menu_item(menu, *item)
        return menu

    def _create_menu_item(self, menu, label, status, handler, \
                         kind=wx.ITEM_NORMAL):
        if not label:
            menu.AppendSeparator()
            return
        menu_item = menu.Append(-1, label, status, kind)
        self.Bind(wx.EVT_MENU, handler, menu_item)

    def _menu_data(self):
        return [('&File', 
                 (('&Import from',
                   (('&Files', 'Import from files',
                    self._on_import_file),
                   ('&Directory', 'Import from directory',
                    self._on_import_dir))),
                  ('&Refresh', 'refresh', self._on_refresh),
                  ('', '', ''),
                  ('&Quit', 'Quit', self._on_quit))),
                ('&Help',
                 (('&About', 'About this program', self._on_about),
                  ('', '', '')))]

    def _on_import_file(self, evt):
        wildcard = 'DICOM (*.dcm)|*.dcm|' \
                   'ACR (*.acr)|*.acr|' \
                   'All files (*.*)|*.*'
        dlg = wx.FileDialog(self, 'Choose dicom files', os.getcwd(),
                            '', wildcard,
                            wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        data_list = []
        if dlg.ShowModal() == wx.ID_OK:
            from server.dicomparser import DicomParser
            parser = DicomParser()
            for path in dlg.GetPaths():
                parser.set_file(path)
                parser.parse()
                data_list.append(parser.get_data())
        dlg.Destroy()

        #
        # test
        #
        server.db.cur.executemany("""INSERT INTO
        images(patient_name, patient_sex, patient_dob,
        body_part, description, modality, study_date, station) VALUES
        (%(patient_name)s, %(patient_sex)s, DATE %(patient_dob)s,
        %(body_part)s, %(description)s, %(modality)s,
        DATE %(study_date)s, %(station)s)""", data_list)
        server.db.conn.commit()
        self._refresh()

    def _on_import_dir(self, evt):
        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

    def _on_refresh(self, evt):
        self._refresh()

    def _on_about(self, evt):
        pass

    def _on_quit(self, evt):
        self.Close()

    def _refresh(self):
        self.list.refresh()
        
        
def main():
    os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
    app = Medicalook()

    reactor.registerWxApp(app)
    reactor.run()

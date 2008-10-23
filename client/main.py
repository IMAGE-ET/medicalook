#!/usr/bin/env python
#
# main.py: main module of Medicalook
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

import sys, os, datetime, time
import wx
import ConfigParser

from twisted.python import log
from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor

import common, utils
from virtual_listctrl import VirtualListCtrl, DataSource
from medproto_client import MedicalookClientFactory
from preferences_dlg import PreferencesDlg

class MedicalookApp(wx.App):
    def __init__(self):
        self.main_frame = None
        wx.App.__init__(self, 0)

    def OnInit(self):
        self.init_preferences()
        self.main_frame = MedicalookBrowser(None, -1, "medicalook")
        self.main_frame.Show()
        self.SetTopWindow(self.main_frame)
        return True

    def init_preferences(self):
        defaults = {
            'host': '202.120.40.93',
            'port': '5213',
            'viewer_path': '',
            'chunk_size': '65536',
            'homepage': 'http://202.120.40.93/wiki/index.php/Medicalook',
            }

        common.config = ConfigParser.ConfigParser(defaults)
        common.config.read(common.config_file)
        if not common.config.has_section('medicalook'):
            common.config.add_section('medicalook')
            common.config.set('medicalook', 'file_dir', common.file_dir)
            f = open(common.config_file, 'w')
            common.config.write(f)
            f.close()

        print "confdir: ", common.confdir
        common.host = common.config.get('medicalook', 'host')
        common.port = common.config.getint('medicalook', 'port')
        common.chunk_size = common.config.getint('medicalook', 'chunk_size')
        common.viewer_path = common.config.get('medicalook', 'viewer_path')
        common.homepage = common.config.get('medicalook', 'homepage')
        common.file_dir = common.config.get('medicalook', 'file_dir')

        common.modality_choices = ('Any', 'CT', 'MR', 'XA', 'CR', 'NM', 'SC')
        common.date_choices = ('Any', 'Today', 'Yesterday', 'Date', 'Range')
        common.sex_choices = ('Any', 'm', 'f')
        common.age_choices = ('Any', 'Age', 'Range')


class MedicalookBrowser(wx.Frame):
    def __init__(self, parent, ID, title        ):
        wx.Frame.__init__(self, parent, ID, title,
                          wx.DefaultPosition, wx.Size(1000, 600))
        self._create_menubar()
        self._create_statusbar()
        panel = wx.Panel(self, -1)
        panel_search = wx.Panel(panel, -1, size=(-1, 100))

        search_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_search.SetSizer(search_sizer)

        basic_sizer = wx.FlexGridSizer(rows=1, cols=8, hgap=5, vgap=5)

        label_name = wx.StaticText(panel_search, -1, "Name")
        field_name = wx.TextCtrl(panel_search, -1, "", size=(250, -1))

        label_modality = wx.StaticText(panel_search, -1, "Modality")
        field_modality = wx.Choice(panel_search, -1,
                                   choices=common.modality_choices)
        field_modality.SetSelection(0)

        label_date = wx.StaticText(panel_search, -1, "Study date")
        field_date = wx.Choice(panel_search, -1,
                               choices=common.date_choices)
        field_date.SetSelection(0)

        date_sizer_first = wx.BoxSizer(wx.HORIZONTAL)
        field_date_first = wx.DatePickerCtrl(panel_search, size=(120, -1),
                                             style=wx.DP_DROPDOWN | \
                                             wx.DP_SHOWCENTURY)
        date_sizer_first.Add(field_date_first, 0,
                             wx.TOP | wx.BOTTOM, 10)

        date_sizer_second = wx.BoxSizer(wx.HORIZONTAL)
        date_label_dash = wx.StaticText(panel_search, -1, "-")
        field_date_second = wx.DatePickerCtrl(panel_search, size=(120, -1),
                                              style=wx.DP_DROPDOWN | \
                                              wx.DP_SHOWCENTURY)
        date_sizer_second.Add(date_label_dash, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        date_sizer_second.Add(field_date_second, 0,
                              wx.TOP | wx.RIGHT | wx.BOTTOM, 10)

        basic_sizer.Add(label_name, 0,
                        wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                        10)
        basic_sizer.Add(field_name, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        basic_sizer.Add(label_modality, 0,
                        wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                        10)
        basic_sizer.Add(field_modality, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        basic_sizer.Add(label_date, 0,
                        wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                        10)
        basic_sizer.Add(field_date, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        basic_sizer.Add(date_sizer_first)
        basic_sizer.Add(date_sizer_second)
        basic_sizer.Hide(date_sizer_first)
        basic_sizer.Hide(date_sizer_second)

        cb = wx.CheckBox(panel_search, -1, 'Advanced query')
        cb.SetValue(False)

        adv_sizer = wx.BoxSizer(wx.VERTICAL)
        firstrow_sizer = wx.BoxSizer(wx.HORIZONTAL)

        label_bodypart = wx.StaticText(panel_search, -1, "Body part")
        field_bodypart = wx.TextCtrl(panel_search, -1, "", size=(100, -1))

        label_sex = wx.StaticText(panel_search, -1, "Patient sex")
        field_sex = wx.Choice(panel_search, -1,
                              choices=common.sex_choices)
        field_sex.SetSelection(0)

        label_age = wx.StaticText(panel_search, -1, "Patient age")
        field_age = wx.Choice(panel_search, -1,
                              choices=common.age_choices)
        field_age.SetSelection(0)

        age_sizer_first = wx.BoxSizer(wx.HORIZONTAL)
        field_age_first = wx.TextCtrl(panel_search, -1, size=(30, -1))
        age_sizer_first.Add(field_age_first, 0,
                             wx.TOP | wx.BOTTOM, 10)

        age_sizer_second = wx.BoxSizer(wx.HORIZONTAL)
        age_label_dash = wx.StaticText(panel_search, -1, "-")
        field_age_second = wx.TextCtrl(panel_search, -1, size=(30, -1))
        age_sizer_second.Add(age_label_dash, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        age_sizer_second.Add(field_age_second, 0,
                              wx.TOP | wx.RIGHT | wx.BOTTOM, 10)

        label_description = wx.StaticText(panel_search, -1, "Description")
        field_description = wx.TextCtrl(panel_search, -1, "", size=(350, -1))

        firstrow_sizer.Add(label_bodypart, 0,
                           wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                           10)
        firstrow_sizer.Add(field_bodypart, 0,
                           wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        firstrow_sizer.Add(label_sex, 0,
                           wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                           10)
        firstrow_sizer.Add(field_sex, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        firstrow_sizer.Add(label_age, 0,
                           wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                           10)

        firstrow_sizer.Add(field_age, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        firstrow_sizer.Add(age_sizer_first)
        firstrow_sizer.Add(age_sizer_second)
        firstrow_sizer.Hide(age_sizer_first)
        firstrow_sizer.Hide(age_sizer_second)

        secondrow_sizer = wx.BoxSizer(wx.HORIZONTAL)
        secondrow_sizer.Add(label_description, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | \
                            wx.LEFT | wx.RIGHT | wx.BOTTOM,
                            10)
        secondrow_sizer.Add(field_description, 0, wx.RIGHT | wx.BOTTOM, 10)

        adv_sizer.Add(firstrow_sizer)
        adv_sizer.Add(secondrow_sizer)

        btn_search = wx.Button(panel_search, -1, "Search", (20, 10))
        btn_recent = wx.Button(panel_search, -1, "Recent", (20, 10))
        btn_reset = wx.Button(panel_search, -1, "Reset", (20, 10))

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_search, 0, wx.ALL, 10)
        btn_sizer.Add(btn_recent, 0, wx.ALL, 10)
        btn_sizer.Add(btn_reset, 0, wx.ALL, 10)

        search_sizer.Add(basic_sizer)
        search_sizer.Add(cb, 0, wx.ALL, 5)
        search_sizer.Add(adv_sizer)
        search_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)

        search_sizer.Hide(adv_sizer, recursive=True)

        self.basic_sizer = basic_sizer
        self.search_sizer = search_sizer
        self.adv_sizer = adv_sizer
        self.firstrow_sizer = firstrow_sizer
        self.date_sizer_first = date_sizer_first
        self.date_sizer_second = date_sizer_second
        self.age_sizer_first = age_sizer_first
        self.age_sizer_second = age_sizer_second

        self.panel = panel
        self.panel_search = panel_search

        self.field_name = field_name
        self.field_modality = field_modality
        self.field_date = field_date
        self.field_date_first = field_date_first
        self.field_date_second = field_date_second
        self.field_bodypart = field_bodypart
        self.field_sex = field_sex
        self.field_age = field_age
        self.field_age_first = field_age_first
        self.field_age_second = field_age_second
        self.field_description = field_description
        self.cb = cb

        self.connector = None
        self.client = MedicalookClientFactory(self)
        self._connect_to_server()
        self.data_source = DataSource()
        self.list = VirtualListCtrl(panel, self.data_source, self.client)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel_search, 0,
                  wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 10)
        sizer.Add(self.list, 1, wx.EXPAND|wx.ALL, 10)

        panel.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self._on_quit)
        self.Bind(wx.EVT_CHOICE, self._on_choose_date, field_date)
        self.Bind(wx.EVT_CHOICE, self._on_choose_age, field_age)
        self.Bind(wx.EVT_BUTTON, self._on_click_search, btn_search)
        self.Bind(wx.EVT_BUTTON, self._on_click_recent, btn_recent)
        self.Bind(wx.EVT_BUTTON, self._on_click_reset, btn_reset)
        self.Bind(wx.EVT_CHECKBOX, self._toggle_advanced_query, cb)
        #self.Bind(wx.EVT_KEY_DOWN, self._on_key, field_name)

        self.Centre()
        self.Show(True)

    def _connect_to_server(self):
        self.connector = reactor.connectTCP(common.host, common.port,
                                            self.client)

    def _on_reconnect(self, evt):
        if self.connector:
            self.connector.disconnect()
        self._connect_to_server()

    def show_error(self, msg):
        dlg = wx.MessageDialog(self, msg, 'Error',
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def _on_key(self, evt):
        print '============================================'
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            self._on.click_search(evt)

    def _toggle_advanced_query(self, evt):
        cb = evt.GetEventObject()
        if cb.GetValue():
            self.search_sizer.Show(self.adv_sizer, recursive=False)
            self._on_choose_age(None)
        else:
            self.search_sizer.Hide(self.adv_sizer, recursive=False)
        self.panel.Layout()

    def _on_choose_date(self, evt):
        c = evt.GetString()
        if c == 'Date':
            self.basic_sizer.Hide(self.date_sizer_second, recursive=True)
            self.basic_sizer.Show(self.date_sizer_first, recursive=True)
        elif c == 'Range':
            self.basic_sizer.Show(self.date_sizer_first, recursive=True)
            self.basic_sizer.Show(self.date_sizer_second, recursive=True)
        else:
            self.basic_sizer.Hide(self.date_sizer_first, recursive=True)
            self.basic_sizer.Hide(self.date_sizer_second, recursive=True)
        self.basic_sizer.Layout()

    def _on_choose_age(self, evt):
        #c = evt.GetString()
        c = str(self.field_age.GetStringSelection())
        if c == 'Age':
            self.firstrow_sizer.Hide(self.age_sizer_second, recursive=True)
            self.firstrow_sizer.Show(self.age_sizer_first, recursive=True)
        elif c == 'Range':
            self.firstrow_sizer.Show(self.age_sizer_first, recursive=True)
            self.firstrow_sizer.Show(self.age_sizer_second, recursive=True)
        else:
            self.firstrow_sizer.Hide(self.age_sizer_first, recursive=True)
            self.firstrow_sizer.Hide(self.age_sizer_second, recursive=True)
        self.firstrow_sizer.Layout()

    def _create_statusbar(self):
        self.statusbar = wx.StatusBar(self, style=wx.SB_FLAT)
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths([-1, -2])
        self.SetStatusBar(self.statusbar)

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

    def _create_menu_item(self, menu, label, status, handler,
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
                  ('Re&connect', '', self._on_reconnect),
                  ('', '', ''),
                  ('&Quit', 'Quit', self._on_quit)
                  )),
                ('&Edit',
                 (('&Refresh', 'refresh', self._on_refresh),
                  ('&Preferences', 'Set your preferences',
                   self._on_preferences),
                  )),
                ('&Help',
                 (('&Website', 'Visit the website', self._on_website),
                  ('', '', ''),
                  ('&About', 'About this program', self._on_about),
                  ))]

    def _on_import_file(self, evt):
        wildcard = 'DICOM (*.dcm)|*.dcm|' \
                   'ACR (*.acr)|*.acr|' \
                   'RAR (*.rar)|*.rar'
        dlg = wx.FileDialog(self, 'Choose dicom files', os.getcwd(),
                            '', wildcard,
                            wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            for path in paths:
                self.client.import_query(path)
        dlg.Destroy()

    def _on_import_dir(self, evt):
        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            paths = utils.locate(path)
            for path in paths:
                if path.endswith('.dcm') or path.endswith('.DCM'):
                    self.client.import_query(path)
        dlg.Destroy()

    def _on_preferences(self, evt):
        dlg = PreferencesDlg(self)
        r = dlg.ShowModal()
        if r == wx.ID_OK:
            val = dlg.GetValue()
            common.host = val['host']
            common.port = val['port']
            common.viewer_path = val['viewer_path']

            common.config.set('medicalook', 'host', common.host)
            common.config.set('medicalook', 'port', common.port)
            common.config.set('medicalook', 'viewer_path',
                              common.viewer_path)
            f = open(common.config_file, 'w')
            common.config.write(f)
            f.close()
        dlg.Destroy()

    def _on_click_search(self, evt):
        val = {}
        if self.field_name.GetValue():
            val['patient_name'] = str(self.field_name.GetValue())
        if self.field_modality.GetCurrentSelection():
            val['modality'] = str(self.field_modality.GetStringSelection())
        d_choice = self.field_date.GetStringSelection()
        if d_choice == "Today":
            val['study_date'] = str(datetime.date.today())
        elif d_choice == "Yesterday":
            val['study_date'] = str(datetime.date.today() \
                                - datetime.timedelta(days=1))
        elif d_choice == "Date":
            val['study_date'] = str(utils.wxdate2pydate(
                self.field_date_first.GetValue()))
        elif d_choice == "Range":
            f = utils.wxdate2pydate(self.field_date_first.GetValue())
            t = utils.wxdate2pydate(self.field_date_second.GetValue())
            val['study_date'] = str(f) + '~' + str(t)

        if self.cb.GetValue():
            if self.field_bodypart.GetValue():
                val['body_part'] = str(self.field_bodypart.GetValue())
            if self.field_sex.GetCurrentSelection():
                val['patient_sex'] = str(self.field_sex.GetStringSelection())
                val['patient_sex'] = val['patient_sex'].lower()
            a_choice = str(self.field_age.GetStringSelection())
            if a_choice == "Age":
                val['patient_dob'] = str(self.field_age_first.GetValue())
            elif a_choice == "Range":
                f = str(self.field_age_first.GetValue())
                t = str(self.field_age_second.GetValue())
                val['patient_dob'] = f + '~' + t
            if self.field_description.GetValue():
                val['description'] = str(self.field_description.GetValue())

        limit = 1000000
        offset = 0

        d = self.client.list_query(val, limit, offset)
        if d: d.addCallback(self._list_response_received)

    def _list_response_received(self, list_data):
        self.data_source.set_rows(list_data)
        if list_data:
            self.list.resize_column()
        else:
            self.list.DeleteAllItems()

    def _on_click_recent(self, evt):
        val = {}

        limit = 1000000
        offset = 0
        d = self.client.list_query(val, limit, offset)
        if d: d.addCallback(self._list_response_received)

    def _on_click_reset(self, evt):
        self.field_name.SetValue('')
        self.field_modality.SetSelection(0)
        self.field_date.SetSelection(0)
        self.field_bodypart.SetValue('')
        self.field_sex.SetSelection(0)
        self.field_age.SetSelection(0)
        self.field_description.SetValue('')

        self.basic_sizer.Hide(self.date_sizer_first, recursive=True)
        self.basic_sizer.Hide(self.date_sizer_second, recursive=True)
        self.basic_sizer.Layout()
        self.firstrow_sizer.Hide(self.age_sizer_first, recursive=True)
        self.firstrow_sizer.Hide(self.age_sizer_second, recursive=True)
        self.firstrow_sizer.Layout()

    def _on_refresh(self, evt):
        self._refresh()

    def _on_website(self, evt):
        wx.LaunchDefaultBrowser(common.homepage)

    def _on_about(self, evt):
        msg = 'Medicalook\n\n \
        author: Wu Zhe <jessewoo at gmail.com>'
        d = wx.MessageDialog(self, msg, 'About', wx.OK)
        d.ShowModal()
        d.Destroy()

    def _on_quit(self, evt):
        reactor.stop()
        self.Close()

    def _refresh(self):
        self.list.refresh()

def main():
    log.startLogging(sys.stdout)

    app = MedicalookApp()
    reactor.registerWxApp(app)

    reactor.run()

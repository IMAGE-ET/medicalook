import os

import wx
import common

class PreferencesDlg(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title="Perferences",
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        panel = wx.Panel(self, -1)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panel_sizer)

        server_box = wx.StaticBox(panel, -1, "Server setting")
        server_sizer = wx.StaticBoxSizer(server_box, wx.VERTICAL)
        server_row_1 = wx.BoxSizer(wx.HORIZONTAL)

        label_host = wx.StaticText(panel, -1, "host")
        field_host = wx.TextCtrl(panel, -1, common.host, size=(250, -1))
        server_row_1.Add(label_host, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 8)
        server_row_1.Add(field_host, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 8)

        server_row_2 = wx.BoxSizer(wx.HORIZONTAL)
        label_port = wx.StaticText(panel, -1, "port")
        field_port = wx.TextCtrl(panel, -1, str(common.port), size=(50, -1))
        server_row_2.Add(label_port, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 8)
        server_row_2.Add(field_port, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 8)

        server_sizer.Add(server_row_1, 0, wx.ALIGN_CENTER, 10)
        server_sizer.Add(server_row_2, 0, wx.ALIGN_LEFT, 10)

        viewer_box = wx.StaticBox(panel, -1, "DICOM viewer setting")
        viewer_sizer = wx.StaticBoxSizer(viewer_box, wx.HORIZONTAL)

        label_path = wx.StaticText(panel, -1, "path")
        field_path = wx.TextCtrl(panel, -1, common.viewer_path,
                                 size=(150, -1))
        btn_path = wx.Button(panel, -1, "browse", (10, 10))
        btn_path.Bind(wx.EVT_BUTTON, self._on_browse)

        viewer_sizer.Add(label_path, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        viewer_sizer.Add(field_path, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        viewer_sizer.Add(btn_path, 0, wx.ALIGN_CENTER|wx.ALL, 8)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(panel, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(panel, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        panel_sizer.Add(server_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        panel_sizer.Add(viewer_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        panel_sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)

        self.field_host = field_host
        self.field_port = field_port
        self.field_path = field_path

        self.Fit()
        self.SetMinSize((350, 270))
        self.SetSize((350, 270))
        self.Center()

    def _on_browse(self, evt):
        dlg = wx.FileDialog(self, 'Choose dicom viewer executable',
                            os.getcwd(), '', 'exe (*.exe)|*.exe')
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.field_path.SetValue(path)
        dlg.Destroy()

    def GetValue(self):
        val = {}
        val['host'] = str(self.field_host.GetValue())
        val['port'] = int(self.field_port.GetValue())
        val['viewer_path'] = str(self.field_path.GetValue())
        return val

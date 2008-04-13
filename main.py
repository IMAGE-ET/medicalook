#!/usr/bin/env python
#
# main.py: main module of Medicalook
# author: Jesse Woo <jessewoo at gmail.com>
# license: GPL

import wx

import common


class Medicalook(wx.App):
    def __init__(self):
        self.main_frame = None
        self.viewer = None
        self.viewer_frame = None
        wx.App.__init__(self, 0)

    def OnInit(self):
        self.init_preferences()

    def init_preferences(self):
        import ConfigParser
        defaults = {
            'server': 'localhost',
            'port': '8888',
            }
        common.config = ConfigParser.ConfigParser(defaults)
        common.config.read(common.config_file)
        if not common.config.has_section('medicalook'):
            common.config.add_section('medicalook')
        common.server = common.config.get('medicalook', 'server')
        common.port = common.config.getint('medicalook', 'port')
        #self.viewer_frame = viewer.DicomViewerFrame(None, '')
        #self.viewer = viewer.DicomViewer()
        self.main_frame = MedicalookBrowser()
        self.SetTopWindow(self.main_frame)


class MedicalookBrowser(wx.Frame):
    def __init__(self, **kwds):
        wx.Frame.__init__(self, None, -1, '')
        


def main():
    os.chdir(os.path.abspath())
    app = Medicalook()

    app.MainLoop()

#!/usr/bin/env python
#
# app.py: server application
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL


from twisted.application import internet, service
from medproto import MedicalookServerFactory

def get_medicalook_service():
    from metadata import columns
    port = 5213
    f = MedicalookServerFactory(columns)
    return internet.TCPServer(port, f)

application = service.Application("medicalookd")

med_service = get_medicalook_service()
med_service.setServiceParent(application)

# -*- coding: utf-8 -*-
from network.network_util import NetworkUtil

class ProxyProcessSession():
    def __init__(self, dialogId, socket):
        self.dialogId = dialogId
        self.lastRevTime = NetworkUtil.getCurTime()
        self.socket = socket
        self.needClose = False

    def close(self):
        self.needClose = True

    def resetRevTime(self):
        self.lastRevTime = NetworkUtil.getCurTime()



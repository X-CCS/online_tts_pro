# -*- coding: utf-8 -*-
from network.network_util import NetworkUtil

__author__ = 'vison'

class ClientSession():
    def __init__(self, dialogId, socket):
        self.dialogId = dialogId
        self.lastRevTime = NetworkUtil.getCurTime()
        self.socket = socket

    def resetRevTime(self):
        self.lastRevTime = NetworkUtil.getCurTime()



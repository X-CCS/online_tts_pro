# -*- coding: utf-8 -*-
import logging
from tornado.websocket import WebSocketHandler, tornado
import json
from server.client_connect_mgr import ClientConnectMgr
from network.error_code import ErrorCode
from network.network_util import NetworkUtil


class MasterHandler(WebSocketHandler):
    #链接检查
    def check_origin(self, origin):
        return True

    #有新的链接
    def open(self):
        #每个新的链接需要一个会话id
        dialogId = self.get_query_argument("dialogId", None)
        if(dialogId is None):
            logging.info("fd:{} dialog is none and disconnect!".format(self))
            self.close(403, NetworkUtil.formatError(ErrorCode.PARAM_IS_NULL))
            return

        #加入链接管理 无需提出逻辑 每次请求都是新的会话
        if(ClientConnectMgr.instance().getSessionByDialogId(dialogId) is not None):
            logging.info("fd:{} dialog:{} exist!".format(self, dialogId))
            self.close(403, NetworkUtil.formatError(ErrorCode.PARAM_ILLEGAL))
            return
        ClientConnectMgr.instance().addConnection(dialogId, self)
        logging.info("fd:{} dialog:{} open!".format(self, dialogId))

    #链接关闭
    def on_close(self):
        ClientConnectMgr.instance().removeConnection(self)
        logging.info("fd:{} on_close!".format(self))

    #收到消息
    def on_message(self, message):
        session = ClientConnectMgr.instance().getSessionBySocket(self)
        if session is None:
            logging.info("fd:{} msg:{} on_message but disconnect!".format(self, message))
            return

        #消息类型特殊处理
        session.lastRevTime = NetworkUtil.getCurTime()
        if(isinstance(message, str)):
            strMessage  = str(message);
            logging.info("fd:{} dialogId:{} strMessage:{} on_message str".format(self, session.dialogId, message))
            ClientConnectMgr.instance().transferMsg(session, strMessage);
        else:
            logging.info("fd:{} dialogId:{} on_message type error".format(self, session.dialogId))

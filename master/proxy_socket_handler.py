# -*- coding: utf-8 -*-
import logging
import traceback
from tornado.websocket import WebSocketHandler, tornado
import json
from master.proxy_connect_mgr import ProxyConnectMgr
from master.assign_proxy_mgr import AssignProxyMgr
from server.client_connect_mgr import ClientConnectMgr
from network.error_code import ErrorCode
from network.network_util import NetworkUtil


class ProxySocketHandler(WebSocketHandler):
    #链接检查
    def check_origin(self, origin):
        return True

    #有新的链接
    def open(self):
        #每个新的链接需要一个会话id
        dialogId = self.get_query_argument("dialogId", None)
        if(dialogId is None):
            logging.info("master fd:{} dialog is none and disconnect!".format(self))
            self.close(403, NetworkUtil.formatError(ErrorCode.PARAM_IS_NULL))
            return

        #加入链接管理 无需提出逻辑 每次请求都是新的会话
        if(ProxyConnectMgr.instance().getSessionByDialogId(dialogId) is not None):
            logging.info("master fd:{} dialog:{} exist!".format(self, dialogId))
            self.close(403, NetworkUtil.formatError(ErrorCode.PARAM_ILLEGAL))
            return
        ProxyConnectMgr.instance().addConnection(dialogId, self)
        logging.info("master fd:{} dialog:{} open!".format(self, dialogId))

    #链接关闭
    def on_close(self):
        ProxyConnectMgr.instance().removeConnection(self)
        logging.info("master fd:{} on_close!".format(self))

    #收到消息
    def on_message(self, message):
        try:
            self.handle_msg(message)
        except:
            logging.error(str(traceback.format_exc()))

    def handle_msg(self, message):
        session = ProxyConnectMgr.instance().getSessionBySocket(self)
        if session is None:
            logging.info("master fd:{} msg:{} on_message but disconnect!".format(self, message))
            return

        #消息类型特殊处理
        session.lastRevTime = NetworkUtil.getCurTime()
        if(isinstance(message, bytes)):
            bytesMessage = bytes(message);
            ClientConnectMgr.instance().transferMsgToClient(session.dialogId, message)
            logging.info("master fd:{} dialogId:{} count:{} on_message byte".format(self, session.dialogId, len(bytesMessage)))
        elif(isinstance(message, str)):
            strMessage  = str(message);
            ClientConnectMgr.instance().transferMsgToClient(session.dialogId, message)
            logging.info("master fd:{} dialogId:{} strMessage:{} on_message str".format(self, session.dialogId, message))
            # 断开连接
            AssignProxyMgr.instance().cleanByProxyDialogId(session.dialogId)
            ProxyConnectMgr.instance().reAssign()
        else:
            logging.info("master fd:{} dialogId:{} on_message type error".format(self, session.dialogId))


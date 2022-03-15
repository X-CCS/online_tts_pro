# -*- coding: utf-8 -*-
import logging
import traceback
from tornado.websocket import WebSocketHandler, tornado
import json
from server.client_connect_mgr import ClientConnectMgr
from network.error_code import ErrorCode
from network.network_util import NetworkUtil
from master.proxy_connect_mgr import ProxyConnectMgr

class ClientSocketHandler(WebSocketHandler):
    #链接检查
    def check_origin(self, origin):
        return True

    #有新的链接
    def open(self):
        #每个新的链接需要一个会话id
        dialogId = self.get_query_argument("dialogId", None)
        isPassSecond = ClientConnectMgr.instance().isPassSecond()
        if(isPassSecond == False):
            logging.info("server fd:{} wait seconds and disconnect!".format(self))
            self.close(403, NetworkUtil.formatError(ErrorCode.FAIL))
            return

        if(dialogId is None):
            logging.info("server fd:{} dialog is none and disconnect!".format(self))
            self.close(403, NetworkUtil.formatError(ErrorCode.PARAM_IS_NULL))
            return

        #加入链接管理 无需提出逻辑 每次请求都是新的会话
        if(ClientConnectMgr.instance().getSessionByDialogId(dialogId) is not None):
            logging.info("server fd:{} dialog:{} exist!".format(self, dialogId))
            self.close(403, NetworkUtil.formatError(ErrorCode.PARAM_ILLEGAL))
            return
        ClientConnectMgr.instance().addConnection(dialogId, self)
        logging.info("server fd:{} dialog:{} open!".format(self, dialogId))

    #链接关闭
    def on_close(self):
        session = ClientConnectMgr.instance().removeConnection(self)
        logging.info("server fd:{} on_close!".format(self))
        # 构造close的事件
        if session is not None:
            msgObj = {}
            msgObj['command'] = 'close'
            ProxyConnectMgr.instance().transferMsgToProxy(session.dialogId, json.dumps(msgObj))

    #收到消息
    def on_message(self, message):
        try:
            self.handle_msg(message)
        except:
            logging.error(str(traceback.format_exc()))

    def handle_msg(self, message):
        session = ClientConnectMgr.instance().getSessionBySocket(self)
        if session is None:
            logging.info("server fd:{} msg:{} on_message but disconnect!".format(self, message))
            return

        #消息类型特殊处理
        session.lastRevTime = NetworkUtil.getCurTime()
        if(isinstance(message, str)):
            strMessage  = str(message);
            logging.info("server fd:{} dialogId:{} strMessage:{} on_message str".format(self, session.dialogId, message))
            ProxyConnectMgr.instance().transferMsgToProxy(session.dialogId, strMessage)
        else:
            logging.info("server fd:{} dialogId:{} on_message type error".format(self, session.dialogId))

# -*- coding: utf-8 -*-
import logging
from master.assign_proxy_mgr import AssignProxyMgr
from network.network_util import NetworkUtil
from server.client_session import ClientSession


class ClientConnectMgr():
    def __init__(self):
        self._cachedsById = {}
        self._cachedsBySocket = {}
        self._startTime = NetworkUtil.getCurTime()

    @staticmethod
    def instance():
        if not hasattr(ClientConnectMgr,'_instance'):
            ClientConnectMgr._instance=ClientConnectMgr()
        return ClientConnectMgr._instance

    # 5秒请求才可以进来
    def isPassSecond(self):
        return NetworkUtil.getCurTime() - self._startTime > 10000

    #添加新的连接 并映射关系
    def addConnection(self, dialogId : str, socket):
        newSession = ClientSession(dialogId, socket);
        self._cachedsById[dialogId] = newSession;
        self._cachedsBySocket[socket] = newSession;
        logging.info("fd:{} dialog:{} addConnection!".format(socket, dialogId))

    #移除链接
    def removeConnection(self, socket):
        if socket in self._cachedsBySocket:
            session = self._cachedsBySocket[socket]
            del self._cachedsBySocket[socket]
            if session.dialogId in self._cachedsById:
                del self._cachedsById[session.dialogId]
                logging.info("fd:{} dialog:{} removeConnection!".format(socket, session.dialogId))
                return session
        return None

    """
    通过会话获取链接
    """
    def getSessionByDialogId(self, dialogId: str)  -> ClientSession:
        if dialogId is not None:
            return self._cachedsById.get(dialogId, None)
        return None

    """
    通过socket获取链接
    """
    def getSessionBySocket(self, socket) -> ClientSession:
        if socket is not None:
            return self._cachedsBySocket.get(socket, None)
        return None

    #转发消息到代理客户端
    def transferMsgToClient(self, proxyDialogId, message):
        clientDialogId = AssignProxyMgr.instance().getClientDialog(proxyDialogId)
        if clientDialogId is None:
            logging.info("server dialog:{} transferMsgToClient clientDialogId is None!".format(clientDialogId))
            return

        clientSession = self.getSessionByDialogId(clientDialogId)
        if clientSession is None:
            logging.info("server dialog:{} transferMsgToClient clientDialogId not exist!".format(clientDialogId))
            return

        if(isinstance(message, bytes)):
            bytesMessage = bytes(message);
            NetworkUtil.writeBtyeToClient(clientSession, message, False)
        elif(isinstance(message, str)):
            strMessage  = str(message);
            NetworkUtil.writeMsgToClient(clientSession, message, True)

    #检查超时逻辑
    def checkTimeout(self):
        curTime = NetworkUtil.getCurTime();
        flushList =[]
        for value in self._cachedsById.values():
            if(curTime - value.lastRevTime > 30000):
                flushList.append(value)
        for session in flushList:
            #remove first
            self.removeConnection(session.socket)
            session.socket.close()
            logging.info("fd:{} dialog:{} removeConnection by checkTimeout!".format(session.socket, session.dialogId))

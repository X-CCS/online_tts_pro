# -*- coding: utf-8 -*-
import json
import logging
from network.network_util import NetworkUtil
from master.proxy_session import ProxySession
from master.assign_proxy_mgr import AssignProxyMgr

class ProxyConnectMgr():
    def __init__(self):
        self._cachedsById = {}
        self._cachedsBySocket = {}

    @staticmethod
    def instance():
        if not hasattr(ProxyConnectMgr,'_instance'):
            ProxyConnectMgr._instance=ProxyConnectMgr()
        return ProxyConnectMgr._instance

    #添加新的连接 并映射关系
    def addConnection(self, dialogId : str, socket):
        newSession = ProxySession(dialogId, socket);
        self._cachedsById[dialogId] = newSession;
        self._cachedsBySocket[socket] = newSession;
        logging.info("master fd:{} dialog:{} addConnection!".format(socket, dialogId))


    #移除链接
    def removeConnection(self, socket):
        if socket in self._cachedsBySocket:
            session = self._cachedsBySocket[socket]
            del self._cachedsBySocket[socket]
            if session.dialogId in self._cachedsById:
                del self._cachedsById[session.dialogId]
                logging.info("master fd:{} dialog:{} removeConnection!".format(socket, session.dialogId))

    """
    通过会话获取链接
    """
    def getSessionByDialogId(self, dialogId: str)  -> ProxySession:
        if dialogId is not None:
            return self._cachedsById.get(dialogId, None)
        return None

    """
    通过socket获取链接
    """
    def getSessionBySocket(self, socket) -> ProxySession:
        if socket is not None:
            return self._cachedsBySocket.get(socket, None)
        return None

    #检查超时逻辑
    def checkTimeout(self):
        curTime = NetworkUtil.getCurTime();

    #转发客户端消息
    def transferMsgToProxy(self, clientDialogId, msgStr):
        msgObj = json.loads(msgStr)
        #合成消息分配代理
        command = msgObj["command"];
        if(command == "compose"):
            AssignProxyMgr.instance().tryAssignClient(clientDialogId)

        proxyDialogId = AssignProxyMgr.instance().getProxyDialog(clientDialogId)
        if proxyDialogId is None:
            logging.info("master dialog:{} transferMsgToProxy proxyDialogId is None msg:{}!".format(clientDialogId, msgStr))
            AssignProxyMgr.instance().addMsgCache(clientDialogId, msgStr)
            return True

        proxySession = self.getSessionByDialogId(proxyDialogId)
        if proxySession is None:
            logging.info("master dialog:{} transferMsgToProxy proxyDialogId not exist msg:{}!".format(proxyDialogId, msgStr))
            return False

        logging.info("master dialog:{} transferMsgToProxy proxyDialogId send:{}!".format(proxyDialogId, msgStr))
        NetworkUtil.writeMsgToClient(proxySession, msgStr, False)
        return  True

    def reAssign(self):
        # 重新分配
        queueItem = AssignProxyMgr.instance().popOne()
        if queueItem is None:
            return

        clientDialogId = queueItem['client_dialogid']
        msgQueue = queueItem['queue']

        for msgStr in msgQueue:
            logging.info("reAssign queueItem dialogId:{} msg:{}".format(clientDialogId, msgStr))
            self.transferMsgToProxy(clientDialogId, msgStr)




# -*- coding: utf-8 -*-
import json
import logging
import threading


class AssignProxyMgr():

    def __init__(self):
        self._client2proxy = {}
        self._proxy2client = {}
        self._noAssignClientQueue = []
        self._noAssignProxyDialog = []

    @staticmethod
    def instance():
        if not hasattr(AssignProxyMgr,'_instance'):
            AssignProxyMgr._instance=AssignProxyMgr()
        return AssignProxyMgr._instance

    def initList(self, dialogList):
        logging.info("initList dialogList={}".format(len(dialogList)))
        for item in dialogList:
            self._noAssignProxyDialog.append(item)

    def tryAssignClient(self, clientDialogId):
        logging.info("tryAssignClient before _proxy2client:{},_client2proxy:{},_noAssignClientQueue:{} _noAssignProxyDialog:{}".format(self._proxy2client, self._client2proxy, self._noAssignClientQueue, self._noAssignProxyDialog))
        if clientDialogId in self._client2proxy:
            logging.info("tryAssignClient clientDialogId:{} has assign proxy".format(clientDialogId))
            return None

        if len(self._noAssignProxyDialog) <= 0:
            queueItem = {}
            queueItem['queue'] = []
            queueItem['client_dialogid'] = clientDialogId
            self._noAssignClientQueue.insert(0, queueItem)
            logging.info("tryAssignClient clientDialogId:{} queueSize:{} not any proxy to assign, and add to cache".format(clientDialogId, len(self._noAssignClientQueue)))
            return None

        proxyDialogId = self._noAssignProxyDialog.pop()
        self._client2proxy[clientDialogId] = proxyDialogId
        self._proxy2client[proxyDialogId] = clientDialogId

        logging.info("tryAssignClient clientDialogId:{} assign to proxyDialogId:{} DialogSize:{}".format(clientDialogId, proxyDialogId, len(self._noAssignProxyDialog)))
        return proxyDialogId

    def popOne(self):
        logging.info("popOne msgQueueSize:{}".format(len(self._noAssignClientQueue)))
        if len(self._noAssignClientQueue) <= 0:
            return None
        queueItem = self._noAssignClientQueue.pop()
        return queueItem

    def cleanByProxyDialogId(self, proxyDialogId):
        if proxyDialogId in self._proxy2client:
            clientDialogId = self._proxy2client[proxyDialogId]
            del self._proxy2client[proxyDialogId]
            del self._client2proxy[clientDialogId]
            logging.info("proxyDialogId:{} clientDialogId:{} dialogQueueSize:{} cleanByProxyDialogId".format(proxyDialogId, clientDialogId, len(self._noAssignProxyDialog)))
            self._noAssignProxyDialog.insert(0, proxyDialogId)
            logging.info("cleanByProxyDialogId after _proxy2client:{},_client2proxy:{},_noAssignClientQueue:{} _noAssignProxyDialog:{}".format(self._proxy2client, self._client2proxy, self._noAssignClientQueue, self._noAssignProxyDialog))
            return proxyDialogId

        logging.info("proxyDialogId:{} cleanByProxyDialogId but fail".format(proxyDialogId))
        return None

    def addMsgCache(self, clientDialogId, msgStr):
        for item in self._noAssignClientQueue:
            if(item['client_dialogid'] == clientDialogId):
                item['queue'].append(msgStr)
                logging.info("clientDialogId:{} msg enter queue".format(clientDialogId))
                return

    def getProxyDialog(self, clientDialogId):
        return self._client2proxy.get(clientDialogId, None)

    def getClientDialog(self, proxyDialogId):
        return self._proxy2client.get(proxyDialogId, None)



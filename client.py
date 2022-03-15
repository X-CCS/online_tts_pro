#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import uuid

from tornado.ioloop import IOLoop
from tornado import gen
from tornado.websocket import websocket_connect

class Client(object):
    def __init__(self, url, dialogId, timeout):
        self.url = url
        self.dialogId = dialogId
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()
        self.ioloop.start()

    @gen.coroutine
    def connect(self):
        print("trying to connect")
        self.ws = yield websocket_connect(self.url)
        self.run()

    @gen.coroutine
    def run(self):
        self.ws.write_message("{\"command\": \"compose\",\"text\": \"碧桂园，碧桂园，碧桂园\"}")
        end = True
        # f = open("{}.pcm".format(self.dialogId), 'wb')
        while True:
            message = yield self.ws.read_message()
            if(isinstance(message, bytes)):
                print("bytes=:{}".format(len(message)))
                # f.write(message)
            elif(isinstance(message, str)):
                print("str=:" + message)
                # f.close()

if __name__ == "__main__":
    dialogId = uuid.uuid4()
    client = Client("ws://127.0.0.1:3000/ws?dialogId={}".format(dialogId), dialogId, 3000)
    client.connect();



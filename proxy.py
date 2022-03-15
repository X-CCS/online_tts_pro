# -*- coding: utf-8 -*-
import json
import logging
import sys
import traceback

from tornado.ioloop import IOLoop
import tornado.web
import tornado.websocket
from tornado import gen
from tornado.websocket import websocket_connect
from logic.proxy_process_session import ProxyProcessSession
from logic.tts_logic import Ttslogic

session = None
@gen.coroutine
def blockConnect(nodeName):
    url = "ws://127.0.0.1:3001/ws?dialogId={}".format(nodeName)
    while True:
        try:
            client = yield websocket_connect(url)
            global session
            session = ProxyProcessSession(nodeName, client)
            logging.info("nodeName:{} connect success".format(nodeName))
            break
        except:
            logging.error(str(traceback.format_exc()))
            logging.info("nodeName:{} connect fail".format(nodeName))
            yield gen.sleep(1)

@gen.coroutine
def mainLoop(nodeName):
    while True:
        if session is None:
            yield gen.sleep(0.1)
            continue
        message = yield session.socket.read_message()
        if(isinstance(message, str)):
            onMsg(session, message);

@gen.coroutine
def onMsg(session : ProxyProcessSession, strMsg : str):
    logging.info("dialogId:{} onMsg={}".format(session.dialogId, strMsg))
    jsonMsg = json.loads(strMsg)
    command = jsonMsg["command"];
    if(command == "compose"):
        Ttslogic.compose(session, jsonMsg)
    elif(command == "close"):
        Ttslogic.interrupt(session, jsonMsg)

def main(nodeName):
    try:
        blockConnect(nodeName)
        mainLoop(nodeName)
    except:
        logging.error(str(traceback.format_exc()))

    IOLoop.instance().start()

if __name__ == "__main__":
    nodeName = "node1"
    if(len(sys.argv) >= 2):
        nodeName = sys.argv[1]
    if nodeName is None:
        logging.info("need to set nodeName")
    else:
        # logging.getLogger().setLevel(logging.DEBUG)
        # fileName = "./logs/logger-{}.log".format(nodeName)

        logging.basicConfig(
            # 日志级别
            level = logging.DEBUG,
            # 日志格式
            # 时间、代码所在文件名、代码行号、日志级别名字、日志信息
            format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
            # 打印日志的时间
            datefmt = '%a, %d %b %Y %H:%M:%S'
        )

        # logging.basicConfig(level=logging.DEBUG, filename=fileName, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        logging.info("chile:{} Process start success".format(nodeName))
        main(nodeName)
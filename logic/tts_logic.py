# -*- coding: utf-8 -*-
import time
import threading
import hashlib
import json
import traceback
import numpy as np
from network.network_util import NetworkUtil
from master.proxy_session import ProxySession
import logging
from logic.tts import managerInst as tts_manager


lock = threading.Lock()
class Ttslogic():

    @staticmethod
    def interrupt(session : ProxySession, jsonObj):
        session.close()


    @staticmethod
    def compose(session : ProxySession, jsonObj):
        check_time = time.time()
        text = jsonObj['text']
        logging.info("stream_convert receive session:{} receive text:{}".format(session.dialogId, text))
        lock.acquire()

        try:
            for data in tts_manager.stream_transfer(text):
                logging.info("data bytes=:{}".format(len(data)))
                session.socket.write_message(data.tobytes(), True)
                # NetworkUtil.writeBtyeToClient(session, data.tobytes())
            logging.info("stream_convert send session:{} receive text:{}".format(session.dialogId, text))
        except:
            logging.error(str(traceback.format_exc()))

        lock.release()
        exec_time = time.time() - check_time
        logging.info("transfer time: {}".format(exec_time))

        jsonRet ={"event":"end","dialogId":session.dialogId,"execTime":exec_time}
        session.socket.write_message(json.dumps(jsonRet))
        # NetworkUtil.writeMsgToClient(session, json.dumps(jsonRet), True)

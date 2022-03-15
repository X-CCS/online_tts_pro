# -*- coding: utf-8 -*-
import logging
import time
from network.error_code import ErrorCode


class NetworkUtil():

    @staticmethod
    def getCurTime():
        t = time.time()
        return (int(round(t * 1000)))

    @staticmethod
    def formatError(error : ErrorCode):
        jsonObj={}
        jsonObj["code"] = error.get_code()
        jsonObj["msg"] = error.get_msg()
        return

    @staticmethod
    def writeMsgToClient(session, message : str, isclose: bool = False):
        session.resetRevTime()
        socket = session.socket
        if socket.ws_connection is None or socket.ws_connection.is_closing():
            logging.info("fd:{} dialogId:{} is close".format(socket, session.dialogId))
            return

        if(isclose):
            socket.write_message(message)
            socket.close()
        else:
            socket.write_message(message)

    @staticmethod
    def writeBtyeToClient(session, bytesMsg : bytes, isclose: bool = False):
        session.resetRevTime()
        socket = session.socket
        if socket.ws_connection is None or socket.ws_connection.is_closing():
            logging.info("fd:{} dialogId:{} is close".format(socket, session.dialogId))
            return

        if(isclose):
            socket.write_message(bytesMsg, True)
            socket.close()
        else:
            socket.write_message(bytesMsg, True)



# -*- coding: utf-8 -*-
import logging
import sys
from tornado.options import define
import tornado.web
import tornado.websocket
from tornado import gen
from master.assign_proxy_mgr import AssignProxyMgr
from server.client_connect_mgr import ClientConnectMgr
from server.client_socket_handler import ClientSocketHandler

from master.proxy_connect_mgr import ProxyConnectMgr
from master.proxy_socket_handler import ProxySocketHandler

# 1、接收合成事件，分配proxy，如果没有可用proxy，则加入缓存。
# 2、没有proxy情况下所有消息都存入队列。
# 3、有proxy情况下所有消息转发proxy。
# 4、收到结束事件，如果没有分配proxy，则直接close掉，如果分配了proxy，则转发事件等待close事件。
# 5、一旦收到close事件，遍历所有缓存结构，判断是否存在空的重新分配。
define("debug", type=bool, default=True, help="debug mode")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/ws", ClientSocketHandler)]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)

    @gen.coroutine
    def checkTimeout(self):
        logging.info("start server timer")
        while True:
            ClientConnectMgr.instance().checkTimeout();
            yield gen.sleep(1)

class Master(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/ws", ProxySocketHandler)]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)

    @gen.coroutine
    def checkTimeout(self):
        logging.info("start master timer")
        while True:
            ProxyConnectMgr.instance().checkTimeout();
            yield gen.sleep(1)

def main(childCount):
    serverPort = 3000
    app = Application()
    app.listen(serverPort)
    app.checkTimeout()
    logging.info("server started port=:{}".format(serverPort))

    masterPort = 3001
    master = Master()
    master.listen(masterPort)
    master.checkTimeout()
    logging.info("master started port=:{}".format(masterPort))

    #启动多个子进程
    proxyQueue=[]
    for num in range(1, childCount+1):
        nodeName = "node{}".format(num)
        logging.info("{} start child count:{}".format(nodeName, childCount))
        proxyQueue.append(nodeName)

    AssignProxyMgr.instance().initList(proxyQueue)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    childCount = 1
    if(len(sys.argv) >= 2):
        childCount = int(sys.argv[1])

    # logging.getLogger().setLevel(logging.DEBUG)
    # logging.basicConfig(level=logging.DEBUG, filename='./logs/logger.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.basicConfig(
        # 日志级别
        level = logging.DEBUG,
        # 日志格式
        # 时间、代码所在文件名、代码行号、日志级别名字、日志信息
        format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        # 打印日志的时间
        datefmt = '%a, %d %b %Y %H:%M:%S'
    )
    main(childCount)
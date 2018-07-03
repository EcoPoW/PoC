import json
import sys
import getopt
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import websocket_connect
from tornado.options import define, options
import threading
import time

import asyncio


class server_thread(threading.Thread):
    def __init__(self, port, peer_ports):
        threading.Thread.__init__(self)
        self.node = Node(port, peer_ports)

    def run(self):
        print("open server")
        self.node.open_server()


async def ser(port):
    print(port)
    server = Application()
    server.listen(port)
    # tornado.ioloop.IOLoop.start()

    server.ioloop.start()


class Node:

    def __init__(self, port, peer_ports):
        self.port = port
        self.peer_ports = peer_ports

    def open_server(self):
        print("server is ready")
        print(self.port)
        server = Application()
        server.listen(self.port)
        server.ioloop.start()
       
    def read_client(self, other_port):
        to_url = "ws://localhost:" + str(other_port)
        client = Client(5)
        client.read(to_url)
        client.ioLoop.start()

    def write_client(self, msg, other_port):
        to_url = "ws://localhost:" + str(other_port)
        client = Client(5)
        client.write(msg, to_url)
        client.ioLoop.start()

    # def open_client(self,other_port):
    #     url="ws://localhost:"+str(other_port)
    #     client = Client(url,5)
    #     client.connect()
    #     client.ioLoop.start()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    ]
        settings = dict(debug=True)
        self.ioloop = tornado.ioloop.IOLoop.instance()

        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    clients = set()

    def check_origin(self, origin):
        return True

    def open(self):
        print("A client connected.")
        MainHandler.clients.add(self)


        print(len(MainHandler.clients))

    def on_close(self):
        print("A client disconnected")
        MainHandler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    def on_message(self, message):
        print(message)
        for c in MainHandler.clients:
            if c != self:
                c.write_message(message)


class Client():

    def __init__(self, timeout):
        self.timeout = timeout
        self.ioLoop = IOLoop.instance()
        self.webSocket = None

    # @gen.coroutine
    # def connect(self, to_url):
    #     print("client trying to connect")

    #     self.webSocket = yield websocket_connect(to_url)

    @gen.coroutine
    def read(self, to_url):
        print("client trying to read msg")
        self.webSocket = yield websocket_connect(to_url)
        while True:

            msg = yield self.webSocket.read_message()
            if msg is None:
                break
            else:
                print(msg)

    @gen.coroutine
    def write(self, msg, to_url):
        self.webSocket = yield websocket_connect(to_url)

        print("client trying to write msg")

        self.webSocket.write_message(msg)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="progrom description")


    parser.add_argument('--port')


    args = parser.parse_args()
    port = args.port


    # node = Node(8080, [8090, 9000])
    # node.open_server()
    #
    n = Node(port,[9999,9991])
    n.open_server()


    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(asyncio.gather(
    #     # factorial("A", 2),
    #     # factorial("B", 3),
    #     # factorial("C", 4),
    #     ser(8080),
    #     ser(9090),
    #     ser(9999),
    # ))
    # loop.close()

    # t = threading.Thread(target=node.open_server())  # 创建线程
    # t.setDaemon(True)  # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
    # t.start()  # 开启线程


    # t1 = threading.Thread(target=n.open_server())
    # t1.setDaemon(True)
    # t1.start()

import subprocess
import time
import socket
import json
import argparse
# import pickle
# from multiprocessing import Process,Pool,Queue,Manager

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/control", ControlHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class ControlHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        print("A client connected.")
        if self not in ControlHandler.clients:
            ControlHandler.clients.add(self)

        print("Clients", len(ControlHandler.clients))

    def on_close(self):
        print("A client disconnected")
        if self in ControlHandler.clients:
            ControlHandler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        print("On Message"+str(msg))
        
        if str(msg).split(";;;")[1] in served_msg:
            print("message served")
            return
        # print(str(msg).split(";;;")[0]+":server")
        print("client number "+str(len(ControlHandler.clients)))

        # for c in main_handler.clients:
        #     if c!=self:
        #         c.write_message(message)
        # with open(port, 'rb') as f:
        #     tree=pickle.load(f)
        # if len(tree[port]) == 0:
        #     return
        # for url in tree[port]:
        #     to_url = "ws://localhost:" + url
        #     webSocket = yield tornado.websocket.websocket_connect(to_url)
        #     webSocket.write_message(str(msg).split(";;;")[0]+";;;"+str(msg).split(";;;")[1])

        # if len(peer) == 0:
        #     return
        # for u in peer.split(","):
        #     if u == str(port):
        #         return
        #     to_url = "ws://localhost:" + u
        #     webSocket = yield tornado.websocket.websocket_connect(to_url)
        #     webSocket.write_message(message.split(";;;")[0]+";;;"+message.split(";;;")[1])


def main():
    global port, control_port

    parser = argparse.ArgumentParser(description="program description")
    # parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    # port = args.port
    control_port = args.control_port

    server = Application()
    server.listen(control_port)
    # tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

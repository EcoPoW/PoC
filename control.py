import subprocess
import time
import socket
import json
import argparse

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen

incremental_port = 8001
known_addresses = set()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/control", ControlHandler),
                    (r"/new", NewHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)

class NewHandler(tornado.web.RequestHandler):
    def get(self):
        global incremental_port
        subprocess.Popen(["python", "node.py", "--port=%s"%incremental_port, "--control_port=8000"])
        self.finish("new node "+str(incremental_port))
        incremental_port += 1

class ControlHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        print("A client connected")
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
        seq = json.loads(msg)
        print("on_message", seq)
        if seq[0] == "ADDRESS":
            addr = tuple(seq[1:3])
            # print(addr)
            known_addresses.add(addr)
            # print(known_addresses)


def main():
    global port, control_port

    parser = argparse.ArgumentParser(description="control description")
    parser.add_argument('--control_port')

    args = parser.parse_args()
    control_port = args.control_port

    server = Application()
    server.listen(control_port)
    # tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

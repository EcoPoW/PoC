from __future__ import print_function

import subprocess
import time
import socket
import json
import argparse
import random

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen

incremental_port = 8001

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/control", ControlHandler),
                    (r"/new_node", NewNodeHandler),
                    (r"/dashboard", DashboardHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)

class NewNodeHandler(tornado.web.RequestHandler):
    def get(self):
        global incremental_port
        subprocess.Popen(["python", "node.py", "--port=%s"%incremental_port, "--control_port=8000"])
        self.finish("new node %s\n" % incremental_port)
        incremental_port += 1

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("")
        self.finish()

class ControlHandler(tornado.websocket.WebSocketHandler):
    known_addresses = dict()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        print("control: node connected")
        # print("Clients", len(ControlHandler.known_addresses))
        self.addr = None

    def on_close(self):
        print("control: node disconnected")
        if self.addr in ControlHandler.known_addresses:
            del ControlHandler.known_addresses[self.addr]

    # def send_to_client(self, msg):
    #     print("send message: %s" % msg)
    #     self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        seq = json.loads(msg)
        print("control on message", seq)
        if seq[0] == u"ADDRESS":
            self.addr = tuple(seq[1:3])
            # print(self.addr)
            known_addresses_list = list(ControlHandler.known_addresses)
            random.shuffle(known_addresses_list)
            self.write_message(json.dumps(["BOOTSTRAP_ADDRESS", known_addresses_list[:3]]))
            ControlHandler.known_addresses[self.addr] = self
            # print(ControlHandler.known_addresses)
        elif seq[0]:
            pass


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

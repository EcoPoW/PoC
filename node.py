import time
import socket
import subprocess
import argparse
import json

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", NodeHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class NodeHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        print(" A client connected", port)
        if self not in NodeHandler.clients:
            NodeHandler.clients.add(self)

        print(len(NodeHandler.clients))

    def on_close(self):
        print("a client disconnected")
        if self in NodeHandler.clients:
            NodeHandler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        print("on message", msg)


control_node = None
def on_connect(future):
    global control_node
    print("on_connect")

    try:
        control_node = future.result()
        control_node.write_message(json.dumps(["ADDRESS", "", port]))
    except:
        print("reconnect ...")
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

def on_message(msg):
    global control_node
    if msg is None:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)
        return

    print("on_message", msg)

def connect():
    print("connect", control_port)
    tornado.websocket.websocket_connect("ws://localhost:%s/control" % control_port, callback=on_connect, on_message_callback=on_message)

def main():
    global port, control_port

    parser = argparse.ArgumentParser(description="node description")
    parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    port = args.port
    control_port = args.control_port

    server = Application()
    server.listen(port)
    tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

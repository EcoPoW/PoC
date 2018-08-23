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
import tornado.httpclient
import tornado.gen


available_branches = set()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", NodeHandler),
                    (r"/available_branches", AvailableBranchesHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class AvailableBranchesHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish({})


class NodeHandler(tornado.websocket.WebSocketHandler):
    children_nodes = dict()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        print("a client connected", port)
        if self not in NodeHandler.children_nodes:
            NodeHandler.children_nodes.add(self)

        # print(len(NodeHandler.children_nodes))

    def on_close(self):
        print("a client disconnected")
        if self in NodeHandler.children_nodes:
            NodeHandler.children_nodes.remove(self)

    def send_to_client(self, msg):
        print("send message: %s" % msg)
        self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        print("on message", msg)


class Connector(object):
    """Websocket Client"""
    parent_nodes = set()

    def __init__(self, ws_uri):
        self.ws_uri = ws_uri
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 1200.0)

    def on_connect(self, future):
        global parent_nodes
        print("on parent connect")

        try:
            self.conn = future.result()
            if self not in parent_nodes:
                parent_nodes.add(self)
            # parent_node.write_message(json.dumps(["ADDRESS", "localhost", port]))
        except:
            print("reconnect ...")
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)


    def on_message(self, msg):
        # global control_node
        if msg is None:
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        print("on parent message", seq)
        if seq[0] == "BOOTSTRAP_ADDRESS":
            print(seq[1])


control_node = None
def on_connect(future):
    global control_node
    # print("on connect")

    try:
        control_node = future.result()
        control_node.write_message(json.dumps(["ADDRESS", "localhost", port]))
    except:
        print("reconnect ...")
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

@tornado.gen.coroutine
def on_message(msg):
    print("node on message", msg)
    global control_node
    global available_branches
    if msg is None:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)
        return

    seq = json.loads(msg)
    print("node on message", seq)
    if seq[0] == "BOOTSTRAP_ADDRESS":
        # print("BOOTSTRAP_ADDRESS", seq)
        if not seq[1]:
            # root node
            available_branches.add(tuple([port, "R"]))
            available_branches.add(tuple([port, "L"]))
            print("available branches", available_branches)
        else:
            pass
            print("fetch", seq[1][0])
            http_client = tornado.httpclient.AsyncHTTPClient()
            # try:
            response = yield http_client.fetch("http://%s:%s/available_branches" % tuple(seq[1][0]))
            # except Exception as e:
            #     print("Error: %s" % e)
            # else:
            print(response.body)

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

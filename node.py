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
current_branch = None

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", NodeHandler),
                    (r"/available_branches", AvailableBranchesHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class AvailableBranchesHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish({"available_branches":list(available_branches)})


class NodeHandler(tornado.websocket.WebSocketHandler):
    children_nodes = dict()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        self.branch = self.get_argument("branch")
        self.remove_node = True
        # print("branch", self.branch)
        if self.branch in NodeHandler.children_nodes:
            print(port, "force disconnect")
            self.remove_node = False
            self.close()
            return

        print(port, "a child connected parent", self.branch)
        if self.branch not in NodeHandler.children_nodes:
            NodeHandler.children_nodes[self.branch] = self


    def on_close(self):
        print(port, "a child disconnected from parent")
        if self.branch in NodeHandler.children_nodes and self.remove_node:
            del NodeHandler.children_nodes[self.branch]
        self.remove_node = True

    # def send_to_client(self, msg):
    #     print("send message: %s" % msg)
    #     self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        print("on message", msg)


class Connector(object):
    """Websocket Client"""
    parent_nodes = set()

    def __init__(self, host, port, branch):
        self.ws_uri = "ws://%s:%s/node?branch=%s&from=%s" % (host, port, branch, port)
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 1200.0)

    def on_connect(self, future):
        global parent_nodes
        print(port, "node connect")

        # try:
        self.conn = future.result()
        if self not in Connector.parent_nodes:
            Connector.parent_nodes.add(self)
        # except:
        #     print(port, "reconnect1 ...")
        #     tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)


    def on_message(self, msg):
        global available_branches
        global current_branch
        if msg is None:
            # print("reconnect2 ...")
            available_branches.remove(current_branch)
            # available_branches = set([tuple(i) for i in branches])
            branches = list(available_branches)
            current_branch = tuple(branches[0])
            host, port, branch = current_branch
            self.ws_uri = "ws://%s:%s/node?branch=%s&from=%s" % (host, port, branch, port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        # print("on parent message", seq)
        # if seq[0] == "BOOTSTRAP_ADDRESS":
        #     print(seq[1])


control_node = None
def on_connect(future):
    global control_node
    # print("on connect")

    try:
        control_node = future.result()
        control_node.write_message(json.dumps(["ADDRESS", "localhost", port]))
    except:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

@tornado.gen.coroutine
def on_message(msg):
    print(port, "node on message", msg)
    global control_node
    global available_branches
    global current_branch
    if msg is None:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)
        return

    seq = json.loads(msg)
    if seq[0] == "BOOTSTRAP_ADDRESS":
        # print("BOOTSTRAP_ADDRESS", seq)
        if not seq[1]:
            # root node
            available_branches.add(tuple(["localhost", port, "R"]))
            available_branches.add(tuple(["localhost", port, "L"]))
            print("available branches", available_branches)
        else:
            print("fetch", seq[1][0])
            http_client = tornado.httpclient.AsyncHTTPClient()
            try:
                response = yield http_client.fetch("http://%s:%s/available_branches" % tuple(seq[1][0]))
            except Exception as e:
                print("Error: %s" % e)
            branches = json.loads(response.body)["available_branches"]
            print([tuple(i) for i in branches])
            available_branches = set([tuple(i) for i in branches])
            current_branch = tuple(branches[0])
            Connector(*branches[0])

def connect():
    print("connect control", control_port, "from", port)
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

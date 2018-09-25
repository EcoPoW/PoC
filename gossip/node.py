from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen

NODE_REDUNDANCY = 1

available_branches = set()
available_buddies = set()
available_children_buddies = dict()
current_branch = None
current_groupid = ""
processed_message_ids = set()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/peer", PeerHandler),
                    (r"/broadcast", BroadcastHandler),
                    (r"/dashboard", DashboardHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class BroadcastHandler(tornado.web.RequestHandler):
    def get(self):
        global current_groupid
        test_msg = ["TEST_MSG", current_groupid, time.time(), uuid.uuid4().hex]

        forward(json.dumps(test_msg))
        self.finish({"test_msg": test_msg})

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        # global available_branches
        # global available_buddies

        branches = list(available_branches)
        branches.sort(key=lambda l:len(l[2]))

        parents = []
        self.write("<br>current_groupid: %s <br>" % current_groupid)
        self.write("<br>available_branches:<br>")
        for branch in branches:
            self.write("%s %s %s <br>" %branch)

        self.write("<br>available_buddies: %s<br>" % len(available_buddies))
        for buddy in available_buddies:
            self.write("%s %s <br>" % buddy)

        self.write("<br>parent_nodes:<br>")
        for node in NodeConnector.parent_nodes:
            self.write("%s %s<br>" %(node.host, node.port))

        self.write("<br>available_children_buddies:<br>")
        for k,vs in available_children_buddies.items():
            self.write("%s<br>" % k)
            for v1,v2 in vs:
                self.write("%s %s<br>" % (v1,v2))

        self.finish()


# connect point from buddy node
class PeerHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        pass


# connector to control center
control_node = None
def on_connect(future):
    global control_node

    try:
        control_node = future.result()
        control_node.write_message(json.dumps(["ADDRESS", current_host, current_port]))
    except:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

@tornado.gen.coroutine
def on_message(msg):
    global control_node
    global available_branches
    global available_buddies
    global current_branch
    global current_groupid
    if msg is None:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)
        return

    seq = json.loads(msg)
    print(current_port, "node on message", seq)
    if seq[0] == "BOOTSTRAP_ADDRESS":
        if not seq[1]:
            # root node
            available_branches.add(tuple([current_host, current_port, "0"]))
            available_branches.add(tuple([current_host, current_port, "1"]))
            current_groupid = ""

        # elif len(seq[1]) < NODE_REDUNDANCY:
        #     print(current_port, "connect to root as buddy", seq[1])
        #     BuddyConnector(*seq[1][0])
        # else:
        #     print(current_port, "fetch", seq[1][0])
        #     http_client = tornado.httpclient.AsyncHTTPClient()
        #     try:
        #         response = yield http_client.fetch("http://%s:%s/available_branches" % tuple(seq[1][0]))
        #     except Exception as e:
        #         print("Error: %s" % e)
        #     result = json.loads(response.body)
        #     branches = result["available_branches"]
        #     branches.sort(key=lambda l:len(l[2]))
        #     print(current_port, "fetch result", [tuple(i) for i in branches])

        #     available_branches = set([tuple(i) for i in branches])
        #     current_branch = tuple(branches[0])
        #     NodeConnector(*branches[0])

def connect():
    print("\n\n")
    print(current_port, "connect control", control_port)
    tornado.websocket.websocket_connect("ws://localhost:%s/control" % control_port, callback=on_connect, on_message_callback=on_message)

def main():
    global current_host
    global current_port
    global control_port
    global available_buddies

    parser = argparse.ArgumentParser(description="node description")
    parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    current_host = "localhost"
    current_port = args.port
    control_port = args.control_port
    available_buddies.add(tuple([current_host, current_port]))

    server = Application()
    server.listen(current_port)
    tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

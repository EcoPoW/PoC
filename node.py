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
current_groupid = ""

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", NodeHandler),
                    (r"/available_branches", AvailableBranchesHandler),
                    (r"/disconnect", DisconnectHandler),
                    (r"/broadcast", BroadcastHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class AvailableBranchesHandler(tornado.web.RequestHandler):
    def get(self):
        global available_branches
        self.finish({"available_branches":list(available_branches)})

class DisconnectHandler(tornado.web.RequestHandler):
    def get(self):
        for connector in Connector.parent_nodes:
            # connector.remove_node = False
            connector.conn.close()
        self.finish({})
        tornado.ioloop.IOLoop.instance().stop()

class BroadcastHandler(tornado.web.RequestHandler):
    def get(self):
        global current_groupid
        test_msg = ["TEST_MSG", current_groupid, time.time()]

        for node in NodeHandler.children_nodes.values():
            node.write_message(json.dumps(test_msg))

        for connector in Connector.parent_nodes:
            connector.conn.write_message(json.dumps(test_msg))

        self.finish({})


# connect point from child node
class NodeHandler(tornado.websocket.WebSocketHandler):
    children_nodes = dict()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        global available_branches

        self.branch = self.get_argument("branch")
        self.from_host = self.get_argument("host")
        self.from_port = self.get_argument("port")
        self.remove_node = True
        # print("branch", self.branch)
        if self.branch in NodeHandler.children_nodes:
            print(port, "force disconnect")
            self.remove_node = False
            self.close()
            return

        print(port, "child connected branch", self.branch)
        if self.branch not in NodeHandler.children_nodes:
            NodeHandler.children_nodes[self.branch] = self

        available_branches.remove(tuple([host, port, self.branch]))
        print(port, "available branches open", available_branches)

        print(port, ["DISCARDED_BRANCHES", [[host, port, self.branch]]])
        for node in NodeHandler.children_nodes.values():
            node.write_message(json.dumps(["DISCARDED_BRANCHES", [[host, port, self.branch]]]))

        for connector in Connector.parent_nodes:
            connector.conn.write_message(json.dumps(["DISCARDED_BRANCHES", [[host, port, self.branch]]]))

        self.write_message(json.dumps(["GROUP_ID", self.branch]))


    def on_close(self):
        global available_branches
        print(port, "child disconnected from parent")
        if self.branch in NodeHandler.children_nodes and self.remove_node:
            del NodeHandler.children_nodes[self.branch]
        self.remove_node = True

        available_branches.add(tuple([host, port, self.branch]))

        for node in NodeHandler.children_nodes.values():
            if node != self:
                node.write_message(json.dumps(["AVAILABLE_BRANCHES", [[host, port, self.branch]]]))

        for connector in Connector.parent_nodes:
            connector.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[host, port, self.branch]]]))

        # print(port, tuple([self.from_host, self.from_port, self.branch+"0"]))
        # print(port, tuple([self.from_host, self.from_port, self.branch+"1"]))

        available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"0"]))
        available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"1"]))

        for node in NodeHandler.children_nodes.values():
            if node != self:
                node.write_message(json.dumps(["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]]]))

        for connector in Connector.parent_nodes:
            connector.conn.write_message(json.dumps(["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]]]))

        print(port, "available branches on_close", available_branches)

    # def send_to_client(self, msg):
    #     print("send message: %s" % msg)
    #     self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        global available_branches
        print(port, "on message from child", msg)
        seq = json.loads(msg)
        if seq[0] == "DISCARDED_BRANCHES":
            # print(seq[1])
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(branch_host, branch_port, branch)
                available_branches.remove(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.children_nodes.values():
                if node != self:
                    node.write_message(msg)

            for connector in Connector.parent_nodes:
                connector.conn.write_message(msg)

            print(port, "available branches on_message", available_branches)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(branch_host, branch_port, branch)
                available_branches.add(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.children_nodes.values():
                if node != self:
                    node.write_message(msg)

            for connector in Connector.parent_nodes:
                connector.conn.write_message(msg)

            print(port, "available branches on_message", available_branches)

        else:
            for node in NodeHandler.children_nodes.values():
                if node != self:
                    node.write_message(msg)

            for connector in Connector.parent_nodes:
                connector.conn.write_message(msg)


# connector to parent node
class Connector(object):
    """Websocket Client"""
    parent_nodes = set()

    def __init__(self, to_host, to_port, branch):
        self.host = to_host
        self.port = to_port
        self.branch = branch
        self.ws_uri = "ws://%s:%s/node?branch=%s&host=%s&port=%s" % (self.host, self.port, self.branch, host, port)
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 10.0)

    def on_connect(self, future):
        global available_branches
        global parent_nodes
        print(port, "node connect")

        # try:
        self.conn = future.result()
        if self not in Connector.parent_nodes:
            Connector.parent_nodes.add(self)
        # except:
        #     print(port, "reconnect1 ...")
        #     tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)

        available_branches.add(tuple([host, port, self.branch+"0"]))
        available_branches.add(tuple([host, port, self.branch+"1"]))

        # for i in NodeHandler.children_nodes.values():
        #     i.write_message(json.dumps(["AVAILABLE_BRANCHES", [[host, port, self.branch+"0"], [host, port, self.branch+"1"]]]))
        self.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[host, port, self.branch+"0"], [host, port, self.branch+"1"]]]))


    def on_message(self, msg):
        global available_branches
        global current_branch
        global current_groupid
        if msg is None:
            # print("reconnect2 ...")
            available_branches.remove(current_branch)
            # available_branches = set([tuple(i) for i in branches])
            branches = list(available_branches)
            current_branch = tuple(branches[0])
            branch_host, branch_port, branch = current_branch
            self.ws_uri = "ws://%s:%s/node?branch=%s&from=%s" % (branch_host, branch_port, branch, branch_port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        print(port, "on message from parent", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(port, branch_host, branch_port, branch)
                available_branches.remove(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.children_nodes.values():
                node.write_message(msg)

            print(port, "available branches", available_branches)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(port, branch_host, branch_port, branch)
                available_branches.add(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.children_nodes.values():
                node.write_message(msg)

            print(port, "available branches", available_branches)

        elif seq[0] == "GROUP_ID":
            print(seq[1])
            current_groupid = seq[1]

        else:
            for node in NodeHandler.children_nodes.values():
                node.write_message(msg)


# connector to control center
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
    global current_groupid
    if msg is None:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)
        return

    seq = json.loads(msg)
    if seq[0] == "BOOTSTRAP_ADDRESS":
        # print("BOOTSTRAP_ADDRESS", seq)
        if not seq[1]:
            # root node
            available_branches.add(tuple([host, port, "0"]))
            available_branches.add(tuple([host, port, "1"]))
            current_groupid = ""
            print(port, "available branches", available_branches)
        else:
            print("fetch", seq[1][0])
            http_client = tornado.httpclient.AsyncHTTPClient()
            try:
                response = yield http_client.fetch("http://%s:%s/available_branches" % tuple(seq[1][0]))
            except Exception as e:
                print("Error: %s" % e)
            branches = json.loads(response.body)["available_branches"]
            print("fetch result", [tuple(i) for i in branches])
            available_branches = set([tuple(i) for i in branches])
            current_branch = tuple(branches[0])
            Connector(*branches[0])

def connect():
    print(port, "connect control", control_port)
    tornado.websocket.websocket_connect("ws://localhost:%s/control" % control_port, callback=on_connect, on_message_callback=on_message)

def main():
    global host
    global port
    global control_port

    parser = argparse.ArgumentParser(description="node description")
    parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    host = "localhost"
    port = args.port
    control_port = args.control_port

    server = Application()
    server.listen(port)
    tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

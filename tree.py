from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid
import functools

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpclient
import tornado.gen

import setting
import miner
import leader


control_port = 0

current_host = None
current_port = None
current_branch = None
current_groupid = ""

available_branches = set()
available_buddies = set()
available_children_buddies = dict()

nodes_neighborhoods = dict()
nodes_parents = dict()

processed_message_ids = set()

def forward(seq):
    # global processed_message_ids

    msg_id = seq[-1]
    if msg_id in processed_message_ids:
        return
    processed_message_ids.add(msg_id)
    msg = json.dumps(seq)

    for child_node in NodeHandler.child_nodes.values():
        # if not child_node.stream.closed:
        child_node.write_message(msg)

    for parent_connector in NodeConnector.parent_nodes:
        # if parent_connector.conn.close_code is not None:
        parent_connector.conn.write_message(msg)

    for buddy_node in BuddyHandler.buddy_nodes:
        # if not buddy_node.stream.closed:
        buddy_node.write_message(msg)

    for buddy_connector in BuddyConnector.buddy_nodes:
        # if buddy_connector.conn.close_code is not None:
        buddy_connector.conn.write_message(msg)


# connect point from child node
class NodeHandler(tornado.websocket.WebSocketHandler):
    child_nodes = dict()

    def check_origin(self, origin):
        return True

    def open(self):
        self.branch = self.get_argument("branch")
        self.from_host = self.get_argument("host")
        self.from_port = self.get_argument("port")
        self.remove_node = True
        if self.branch in NodeHandler.child_nodes:
            print(current_port, "force disconnect")
            self.remove_node = False
            self.close()

            message = ["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]], uuid.uuid4().hex]
            forward(message)
            return

        print(current_port, "child connected branch", self.branch)
        if self.branch not in NodeHandler.child_nodes:
            NodeHandler.child_nodes[self.branch] = self

        if tuple([current_host, current_port, self.branch]) in available_branches:
            available_branches.remove(tuple([current_host, current_port, self.branch]))

        message = ["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]], uuid.uuid4().hex]
        forward(message)

        buddies = list(available_children_buddies.get(self.branch, set()))
        message = ["GROUP_ID", self.branch, buddies, uuid.uuid4().hex]
        self.write_message(json.dumps(message))
        available_children_buddies.setdefault(self.branch, set()).add((self.from_host, self.from_port))

    def on_close(self):
        print(current_port, "child disconnected from parent")
        if self.branch in NodeHandler.child_nodes and self.remove_node:
            del NodeHandler.child_nodes[self.branch]
        self.remove_node = True

        available_branches.add(tuple([current_host, current_port, self.branch]))

        message = ["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]], uuid.uuid4().hex]
        forward(message)

        if tuple([self.from_host, self.from_port, self.branch+"0"]) in available_branches:
            available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"0"]))
        if tuple([self.from_host, self.from_port, self.branch+"1"]) in available_branches:
            available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"1"]))

        message = ["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]], uuid.uuid4().hex]
        forward(message)

    @tornado.gen.coroutine
    def on_message(self, msg):
        global current_groupid

        seq = json.loads(msg)
        # print(current_port, "on message from child", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                available_branches.add(tuple([branch_host, branch_port, branch]))

        elif seq[0] == "GROUP_ID_FOR_NEIGHBOURHOODS":
            groupid = seq[1]
            print(current_port, "GROUP_ID_FOR_NEIGHBOURHOODS", current_groupid, groupid)

        elif seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        elif seq[0] == "NEW_TX":
            if (current_host, current_port) in leader.current_leaders:
                leader.transactions.append(seq)
                print(current_port, "txid", seq[1]["transaction"]["txid"])

        forward(seq)


# connector to parent node
class NodeConnector(object):
    """Websocket Client"""
    parent_nodes = set()

    def __init__(self, to_host, to_port, branch):
        self.host = to_host
        self.port = to_port
        self.branch = branch
        self.ws_uri = "ws://%s:%s/node?branch=%s&host=%s&port=%s" % (self.host, self.port, self.branch, current_host, current_port)
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 10.0)

    def close(self):
        if self in NodeConnector.parent_nodes:
            NodeConnector.parent_nodes.remove(self)
        self.conn.close()

    def on_connect(self, future):
        print(current_port, "node connect")

        try:
            self.conn = future.result()
            if self not in NodeConnector.parent_nodes:
                NodeConnector.parent_nodes.add(self)

            available_branches.add(tuple([current_host, current_port, self.branch+"0"]))
            available_branches.add(tuple([current_host, current_port, self.branch+"1"]))

            message = ["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]], uuid.uuid4().hex]
            self.conn.write_message(json.dumps(message))

            message = ["GROUP_ID_FOR_NEIGHBOURHOODS", current_groupid, list(available_buddies), uuid.uuid4().hex]
            self.conn.write_message(json.dumps(message))

        except:
            print(current_port, "NodeConnector reconnect ...")
            # tornado.ioloop.IOLoop.instance().call_later(1.0, bootstrap)
            # tornado.ioloop.IOLoop.instance().call_later(1.0, functools.partial(bootstrap, (self.host, self.port)))
            return

    @tornado.gen.coroutine
    def on_message(self, msg):
        global available_buddies
        global current_branch
        global current_groupid

        if msg is None:
            # print("reconnect2 ...")
            if current_branch in available_branches:
                available_branches.remove(current_branch)
            # available_branches = set([tuple(i) for i in branches])
            branches = list(available_branches)
            current_branch = tuple(branches[0])
            branch_host, branch_port, branch = current_branch
            self.ws_uri = "ws://%s:%s/node?branch=%s&host=%s&port=%s" % (branch_host, branch_port, branch, current_host, current_port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        # print(current_port, "on message from parent", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

            # for node in NodeHandler.child_nodes.values():
            #     node.write_message(msg)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                available_branches.add(tuple([branch_host, branch_port, branch]))

            # for node in NodeHandler.child_nodes.values():
            #     node.write_message(msg)

        elif seq[0] == "GROUP_ID":
            current_groupid = seq[1]
            available_buddies = available_buddies.union(set([tuple(i) for i in seq[2]]))
            buddies_left = available_buddies - set([tuple([current_host, current_port])])
            buddies_left = buddies_left - set([(i.host, i.port) for i in BuddyConnector.buddy_nodes])
            buddies_left = buddies_left - set([(i.from_host, i.from_port) for i in BuddyHandler.buddy_nodes])
            for h, p in buddies_left:
                BuddyConnector(h, p)

            available_children_buddies.setdefault(current_groupid, set()).add((current_host, current_port))
            print(current_port, "GROUP_ID", current_groupid, seq[3])
            # return

        elif seq[0] == "GROUP_ID_FOR_NEIGHBOURHOODS":
            groupid = seq[1]
            print(current_port, "GROUP_ID_FOR_NEIGHBOURHOODS", current_groupid, groupid)

        elif seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        elif seq[0] == "NEW_TX":
            if (current_host, current_port) in leader.current_leaders:
                leader.transactions.append(seq)
                print(current_port, "txid", seq[1]["transaction"]["txid"])

        # else:
        forward(seq)


# connect point from buddy node
class BuddyHandler(tornado.websocket.WebSocketHandler):
    buddy_nodes = set()

    def check_origin(self, origin):
        return True

    def open(self):
        self.from_host = self.get_argument("host")
        self.from_port = self.get_argument("port")
        self.remove_node = True
        if False: #temp disable force disconnect
            print(current_port, "buddy force disconnect")
            self.remove_node = False
            self.close()
            return

        print(current_port, "buddy connected")
        if self not in BuddyHandler.buddy_nodes:
            BuddyHandler.buddy_nodes.add(self)

        available_buddies.add(tuple([self.from_host, self.from_port]))
        message = ["GROUP_ID_FOR_BUDDY", current_groupid, list(available_buddies), uuid.uuid4().hex]
        self.write_message(json.dumps(message))

        # maybe it's wrong, we should tell buddy all the available branches existing
        message = ["AVAILABLE_BRANCHES", [[current_host, current_port, current_groupid+"0"], [current_host, current_port, current_groupid+"1"]], uuid.uuid4().hex]
        self.write_message(json.dumps(message))

    def on_close(self):
        print(current_port, "buddy disconnected")
        if self in BuddyHandler.buddy_nodes and self.remove_node:
            BuddyHandler.buddy_nodes.remove(self)
        self.remove_node = True

    @tornado.gen.coroutine
    def on_message(self, msg):
        seq = json.loads(msg)
        print(current_port, "on message from buddy connector", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                available_branches.add(tuple([branch_host, branch_port, branch]))
                available_children_buddies.setdefault(branch[:-1], set()).add((branch_host, branch_port))

        elif seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        forward(seq)


# connector to buddy node
class BuddyConnector(object):
    """Websocket Client"""
    buddy_nodes = set()

    def __init__(self, to_host, to_port):
        self.host = to_host
        self.port = to_port
        self.ws_uri = "ws://%s:%s/buddy?host=%s&port=%s" % (self.host, self.port, current_host, current_port)
        self.branch = None
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 1000.0)

    def close(self):
        if self in BuddyConnector.buddy_nodes:
            BuddyConnector.buddy_nodes.remove(self)
        self.conn.close()

    def on_connect(self, future):
        print(current_port, "buddy connect")

        try:
            self.conn = future.result()
            if self not in BuddyConnector.buddy_nodes:
                BuddyConnector.buddy_nodes.add(self)
        except:
            print(current_port, "reconnect buddy ...")
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)

        if self.branch is not None:
            message = ["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]], uuid.uuid4().hex]
            self.conn.write_message(json.dumps(message))

    def on_message(self, msg):
        global available_branches
        global available_buddies
        global available_children_buddies

        if msg is None:
            self.ws_uri = "ws://%s:%s/buddy?host=%s&port=%s" % (self.host, self.port, current_host, current_port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        print(current_port, "on message from buddy", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

            # for node in NodeHandler.child_nodes.values():
            #     node.write_message(msg)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                available_branches.add(tuple([branch_host, branch_port, branch]))
                available_children_buddies.setdefault(branch[:-1], set()).add((branch_host, branch_port))

            # for node in NodeHandler.child_nodes.values():
            #     node.write_message(msg)

        elif seq[0] == "GROUP_ID_FOR_BUDDY":
            current_groupid = self.branch = seq[1]
            available_branches.add(tuple([current_host, current_port, current_groupid+"0"]))
            available_branches.add(tuple([current_host, current_port, current_groupid+"1"]))

            available_buddies = available_buddies.union(set([tuple(i) for i in seq[2]]))
            buddies_left = available_buddies - set([tuple([current_host, current_port])])
            buddies_left = buddies_left - set([(i.host, i.port) for i in BuddyConnector.buddy_nodes])
            buddies_left = buddies_left - set([(i.from_host, i.from_port) for i in BuddyHandler.buddy_nodes])
            for h, p in buddies_left:
                BuddyConnector(h, p)

            if self.conn is not None:
                message = ["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]], uuid.uuid4().hex]
                self.conn.write_message(json.dumps(message))
            return

        elif seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        # else:
        forward(seq)

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
def bootstrap(addr):
    global available_branches

    print(current_port, "fetch", addr)
    http_client = tornado.httpclient.AsyncHTTPClient()
    try:
        response = yield http_client.fetch("http://%s:%s/available_branches" % tuple(addr))
    except Exception as e:
        print("Error: %s" % e)
    result = json.loads(response.body)
    branches = result["available_branches"]
    branches.sort(key=lambda l:len(l[2]))
    print(current_port, "fetch result", [tuple(i) for i in branches])

    if branches:
        available_branches = set([tuple(i) for i in branches])
        current_branch = tuple(branches[0])
        NodeConnector(*branches[0])
    else:
        tornado.ioloop.IOLoop.instance().call_later(1.0, functools.partial(bootstrap, addr))

@tornado.gen.coroutine
def on_message(msg):
    global available_branches
    # global available_buddies
    # global available_children_buddies

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

        elif len(seq[1]) < setting.NODE_REDUNDANCY:
            print(current_port, "connect to root as buddy", seq[1])
            BuddyConnector(*seq[1][0])

        else:
            bootstrap(seq[1][0])

def connect():
    print("\n\n")
    print(current_port, "connect control", control_port)
    tornado.websocket.websocket_connect("ws://localhost:%s/control" % control_port, callback=on_connect, on_message_callback=on_message)

def main():
    global current_host
    global current_port
    global control_port

    parser = argparse.ArgumentParser(description="node description")
    parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    current_host = "localhost"
    current_port = args.port
    control_port = args.control_port
    available_buddies.add(tuple([current_host, current_port]))

if __name__ == '__main__':
    print("run python node.py pls")

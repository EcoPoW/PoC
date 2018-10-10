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
import tornado.httpclient
import tornado.gen

import setting
import tree
import node

working = False

def forward(seq):
    # global processed_message_ids

    # msg_id = seq[-1]
    # if msg_id in processed_message_ids:
    #     return
    # processed_message_ids.add(msg_id)
    msg = json.dumps(seq)

    # for child_node in NodeHandler.child_nodes.values():
    #     child_node.write_message(msg)

    # for parent_connector in NodeConnector.parent_nodes:
    #     parent_connector.conn.write_message(msg)

    for leader_node in LeaderHandler.leader_nodes:
        leader_node.write_message(msg)

    for leader_connector in LeaderConnector.leader_nodes:
        leader_connector.conn.write_message(msg)


# connect point from leader node
class LeaderHandler(tornado.websocket.WebSocketHandler):
    leader_nodes = set()

    def check_origin(self, origin):
        return True

    def open(self):
        self.from_host = self.get_argument("host")
        self.from_port = self.get_argument("port")
        # self.remove_node = True
        # if False: #temp disable force disconnect
        #     print(tree.current_port, "leader force disconnect")
        #     self.remove_node = False
        #     self.close()
        #     return

        print(tree.current_port, "leader connected")
        if self not in LeaderHandler.leader_nodes:
            LeaderHandler.leader_nodes.add(self)

        # available_buddies.add(tuple([self.from_host, self.from_port]))
        # message = ["GROUP_ID_FOR_BUDDY", tree.current_groupid, list(available_buddies), uuid.uuid4().hex]
        # self.write_message(json.dumps(message))

        # maybe it's wrong, we should tell leader all the available branches existing
        # message = ["AVAILABLE_BRANCHES", [[tree.current_host, tree.current_port, tree.current_groupid+"0"], [tree.current_host, tree.current_port, tree.current_groupid+"1"]], uuid.uuid4().hex]
        # self.write_message(json.dumps(message))

    def on_close(self):
        print(tree.current_port, "leader disconnected")
        if self in LeaderHandler.leader_nodes: # and self.remove_node
            LeaderHandler.leader_nodes.remove(self)
        # self.remove_node = True

    @tornado.gen.coroutine
    def on_message(self, msg):
        seq = json.loads(msg)
        print(tree.current_port, "on message from leader connector", seq)
        # if seq[0] == "DISCARDED_BRANCHES":
        #     for i in seq[1]:
        #         branch_host, branch_port, branch = i
        #         if tuple([branch_host, branch_port, branch]) in available_branches:
        #             available_branches.remove(tuple([branch_host, branch_port, branch]))

        # elif seq[0] == "AVAILABLE_BRANCHES":
        #     for i in seq[1]:
        #         branch_host, branch_port, branch = i
        #         available_branches.add(tuple([branch_host, branch_port, branch]))
        #         available_children_buddies.setdefault(branch[:-1], set()).add((branch_host, branch_port))

        if seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        forward(seq)


# connector to leader node
class LeaderConnector(object):
    """Websocket Client"""
    leader_nodes = set()

    def __init__(self, to_host, to_port):
        self.host = to_host
        self.port = to_port
        self.ws_uri = "ws://%s:%s/leader?host=%s&port=%s" % (self.host, self.port, tree.current_host, tree.current_port)
        # self.branch = None
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 1000.0)

    def close(self):
        if self in LeaderConnector.leader_nodes:
            LeaderConnector.leader_nodes.remove(self)
        self.conn.close()

    def on_connect(self, future):
        print(tree.current_port, "leader connect")

        try:
            self.conn = future.result()
            if self not in LeaderConnector.leader_nodes:
                LeaderConnector.leader_nodes.add(self)
        except:
            print(tree.current_port, "reconnect leader ...")
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)

        # if self.branch is not None:
        #     message = ["AVAILABLE_BRANCHES", [[tree.current_host, tree.current_port, self.branch+"0"], [tree.current_host, tree.current_port, self.branch+"1"]], uuid.uuid4().hex]
        #     self.conn.write_message(json.dumps(message))

    def on_message(self, msg):
        # global available_branches
        # global available_buddies
        # global available_children_buddies

        if msg is None:
            self.ws_uri = "ws://%s:%s/leader?host=%s&port=%s" % (self.host, self.port, tree.current_host, tree.current_port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        print(tree.current_port, "on message from leader", seq)
        # if seq[0] == "DISCARDED_BRANCHES":
        #     for i in seq[1]:
        #         branch_host, branch_port, branch = i
        #         if tuple([branch_host, branch_port, branch]) in available_branches:
        #             available_branches.remove(tuple([branch_host, branch_port, branch]))

        #     # for node in NodeHandler.child_nodes.values():
        #     #     node.write_message(msg)

        # elif seq[0] == "AVAILABLE_BRANCHES":
        #     for i in seq[1]:
        #         branch_host, branch_port, branch = i
        #         available_branches.add(tuple([branch_host, branch_port, branch]))
        #         available_children_buddies.setdefault(branch[:-1], set()).add((branch_host, branch_port))

        #     # for node in NodeHandler.child_nodes.values():
        #     #     node.write_message(msg)

        # if seq[0] == "GROUP_ID_FOR_BUDDY":
        #     current_groupid = self.branch = seq[1]
        #     available_branches.add(tuple([tree.current_host, tree.current_port, tree.current_groupid+"0"]))
        #     available_branches.add(tuple([tree.current_host, tree.current_port, tree.current_groupid+"1"]))

        #     available_buddies = available_buddies.union(set([tuple(i) for i in seq[2]]))
        #     buddies_left = available_buddies - set([tuple([tree.current_host, tree.current_port])])
        #     buddies_left = buddies_left - set([(i.host, i.port) for i in LeaderConnector.leader_nodes])
        #     buddies_left = buddies_left - set([(i.from_host, i.from_port) for i in LeaderHandler.leader_nodes])
        #     for h, p in buddies_left:
        #         LeaderConnector(h, p)

        #     if self.conn is not None:
        #         message = ["AVAILABLE_BRANCHES", [[tree.current_host, tree.current_port, self.branch+"0"], [tree.current_host, tree.current_port, self.branch+"1"]], uuid.uuid4().hex]
        #         self.conn.write_message(json.dumps(message))
        #     return

        if seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        # else:
        forward(seq)

def mining():
    # global working
    # print(tree.current_port, working)
    if working:
        tornado.ioloop.IOLoop.instance().call_later(1, mining)
    else:
        # time to kill all the connected connectors in handler
        while LeaderHandler.leader_nodes:
            LeaderHandler.leader_nodes.pop().close()
        while LeaderConnector.leader_nodes:
            LeaderConnector.leader_nodes.pop().close()

def start(other_leaders):
    print(tree.current_port, [i[1] for i in other_leaders])
    for other_leader_addr in other_leaders:
        LeaderConnector(*other_leader_addr)
    tornado.ioloop.IOLoop.instance().add_callback(mining)

# def main():
#     # print(tree.current_port, setting.NODE_REDUNDANCY)
#     pass

if __name__ == '__main__':
    # main()
    print("run python node.py pls")

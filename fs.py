from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid

import tornado.web
# import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
# import tornado.httpclient
import tornado.gen

from ecdsa import VerifyingKey, NIST384p


import setting
import tree
import miner
import leader
import database


class ObjectHandler(tornado.web.RequestHandler):
    def get(self):
        branches = list(tree.available_branches)

        # parents = []
        # for node in tree.NodeConnector.parent_nodes:
        #     parents.append([node.host, node.port])
        self.finish({"available_branches": branches,
                     "buddy":len(tree.available_buddies),
                     #"parents": parents,
                     "group_id": tree.current_groupid})

class UserHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_argument("user_id")
        signature = self.get_argument("signature")
        timestamp = self.get_argument("timestamp")

        vk = VerifyingKey.from_string(bytes.fromhex(str(user_id)), curve=NIST384p)
        test = vk.verify(bytes.fromhex(str(signature)), timestamp.encode("utf8"))
        # check database if this user located at current node
        # if not, query to get node id for the user
        # if not existing, query for the replicated

        self.finish({"test": test})

def main():
    pass

if __name__ == '__main__':
    # main()
    print("run python node.py pls")

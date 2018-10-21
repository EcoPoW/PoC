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

# from ecdsa import VerifyingKey, NIST384p
from umbral import pre, keys, signing

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

        public_key = keys.UmbralPublicKey.from_bytes(bytes.fromhex(str(user_id)))
        sig = signing.Signature.from_bytes(bytes.fromhex(str(signature)))
        # vk = VerifyingKey.from_string(bytes.fromhex(str(user_id)), curve=NIST384p)
        assert sig.verify(timestamp.encode("utf8"), public_key)
        # check database if this user located at current node
        # if not, query to get node id for the user
        # if not existing, query for the replicated

        res = {"user_id": user_id}
        user = database.connection.get("SELECT * FROM "+tree.current_port+"users WHERE user_id = %s ORDER BY replication_id ASC LIMIT 1", user_id)
        if user:
            res["user"] = user
        else:
            user_bin = bin(int(user_id[2:], 16))[2:].zfill(64*4)
            print(tree.current_port, user_id[2:], user_bin)

            group_ids = tree.node_neighborhoods.keys()
            distance = 0
            for i in group_ids:
                new_distance = tree.group_distance(i, user_bin)
                if new_distance < distance or not distance:
                    distance = new_distance 
                    group_id = i
                # print(tree.current_port, i, new_distance)
            print(tree.current_port, tree.current_groupid, group_id, distance)
            res["node"] = [group_id, tree.node_neighborhoods[group_id]]

        self.finish(res)

def main():
    pass

if __name__ == '__main__':
    # main()
    print("run python node.py pls")

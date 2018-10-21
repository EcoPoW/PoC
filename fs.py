from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid
import hashlib

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

transactions = []
nonce = 0
def mining():
    global nonce

    longest = miner.longest_chain()
    # print(longest)
    if longest:
        longest_hash = longest[-1].hash
        difficulty = longest[-1].difficulty
        data = longest[-1].data
        identity = longest[-1].identity
        recent = longest[-3:]
        # print(recent)
        if len(recent) * setting.BLOCK_INTERVAL_SECONDS > recent[-1].timestamp - recent[0].timestamp:
            new_difficulty = min(255, difficulty + 1)
        else:
            new_difficulty = max(1, difficulty - 1)

        # if tree.current_port in [i.identity for i in longest[-6:]]:
        #     return

    else:
        longest_hash, difficulty, new_difficulty, data, identity = "0"*64, 1, 1, "", ""

    if not transactions:
        return
    print(transactions)
    transaction = transactions[0]
    msg_header, user_id, folder, timestamp, msg_id = transaction
    if msg_id in [i["identity"] for i in longest or []]:
        transactions.pop(0)
        return

    for i in range(100):
        block_hash = hashlib.sha256((identity + data + longest_hash + str(new_difficulty) + user_id + str(nonce)).encode('utf8')).hexdigest()
        if int(block_hash, 16) < int("1" * (256-difficulty), 2):
            if longest:
                print(len(longest), longest[-1].timestamp, longest[0].timestamp, longest[-1].timestamp - longest[0].timestamp)
            # db.execute("UPDATE chain SET hash = %s, prev_hash = %s, nonce = %s, wallet_address = %s WHERE id = %s", block_hash, longest_hash, nonce, wallet_address, last.id)
            # database.connection.execute("INSERT INTO "+tree.current_port+"chain (hash, prev_hash, nonce, difficulty, identity, timestamp, data) VALUES (%s, %s, %s, %s, '')", block_hash, longest_hash, nonce, difficulty, str(tree.current_port))

            message = ["NEW_BLOCK", block_hash, longest_hash, nonce, new_difficulty, msg_id, int(time.time()), {"folder": folder, "user_id": user_id, "by": tree.current_port}, uuid.uuid4().hex]
            tree.forward(message)
            # print(tree.current_port, "mining", nonce, block_hash)
            nonce = 0
            transactions.pop(0)
            break

        nonce += 1


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
        # user = database.connection.get("SELECT * FROM "+tree.current_port+"users WHERE user_id = %s ORDER BY replication_id ASC LIMIT 1", user_id)
        # if user:
        #     res["user"] = user
        # else:
        #     user_bin = bin(int(user_id[2:], 16))[2:].zfill(64*4)
        #     print(tree.current_port, user_id[2:], user_bin)

        #     group_ids = tree.node_neighborhoods.keys()
        #     distance = 0
        #     for i in group_ids:
        #         new_distance = tree.group_distance(i, user_bin)
        #         if new_distance < distance or not distance:
        #             distance = new_distance 
        #             group_id = i
        #     print(tree.current_port, tree.current_groupid, group_id, distance)
        #     res["node"] = [group_id, tree.node_neighborhoods[group_id]]

        tree.forward(["UPDATE_HOME", user_id, {}, time.time(), uuid.uuid4().hex])

        self.finish(res)

def main():
    print(tree.current_port, "fs")
    mining_task = tornado.ioloop.PeriodicCallback(mining, 1000) # , jitter=0.5
    mining_task.start()

if __name__ == '__main__':
    # main()
    print("run python node.py pls")

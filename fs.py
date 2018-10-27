from __future__ import print_function

import os
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
    msg_header, user_id, data, timestamp, msg_id = transaction
    if msg_id in [i["identity"] for i in longest or []]:
        transactions.pop(0)
        return

    for i in range(100):
        block_hash = hashlib.sha256((identity + json.dumps(data) + longest_hash + str(difficulty) + str(nonce)).encode('utf8')).hexdigest()
        if int(block_hash, 16) < int("1" * (256-difficulty), 2):
            if longest:
                print(len(longest), longest[-1].timestamp, longest[0].timestamp, longest[-1].timestamp - longest[0].timestamp)
            # db.execute("UPDATE chain SET hash = %s, prev_hash = %s, nonce = %s, wallet_address = %s WHERE id = %s", block_hash, longest_hash, nonce, wallet_address, last.id)
            # database.connection.execute("INSERT INTO chain"+tree.current_port+" (hash, prev_hash, nonce, difficulty, identity, timestamp, data) VALUES (%s, %s, %s, %s, '')", block_hash, longest_hash, nonce, difficulty, str(tree.current_port))

            message = ["NEW_BLOCK", block_hash, longest_hash, nonce, new_difficulty, msg_id, int(time.time()), data, uuid.uuid4().hex]
            tree.forward(message)
            # print(tree.current_port, "mining", nonce, block_hash)
            nonce = 0
            transactions.pop(0)
            break

        nonce += 1

class CapsuleHandler(tornado.web.RequestHandler):
    def get(self):
        object_hash = self.get_argument("hash")
        user_id = self.get_argument("user_id")
        timestamp = self.get_argument("timestamp")
        signature = self.get_argument("signature")

        vk = keys.UmbralPublicKey.from_bytes(bytes.fromhex(str(user_id)))
        sig = signing.Signature.from_bytes(bytes.fromhex(str(signature)))
        assert sig.verify((object_hash+timestamp).encode("utf8"), vk)

        capsule = open("data/%s/%s_capsule" % (user_id, object_hash), "rb").read()
        self.finish(capsule)


class ObjectHandler(tornado.web.RequestHandler):
    def get(self):
        object_hash = self.get_argument("hash")
        user_id = self.get_argument("user_id")
        timestamp = self.get_argument("timestamp")
        signature = self.get_argument("signature")

        vk = keys.UmbralPublicKey.from_bytes(bytes.fromhex(str(user_id)))
        sig = signing.Signature.from_bytes(bytes.fromhex(str(signature)))
        assert sig.verify((object_hash+timestamp).encode("utf8"), vk)

        content = open("data/%s/%s" % (user_id, object_hash), "rb").read()
        self.finish(content)

    def post(self):
        object_hash = self.get_argument("hash")
        user_id = self.get_argument("user_id")
        timestamp = self.get_argument("timestamp")
        signature = self.get_argument("signature")

        vk = keys.UmbralPublicKey.from_bytes(bytes.fromhex(str(user_id)))
        sig = signing.Signature.from_bytes(bytes.fromhex(str(signature)))
        assert sig.verify((object_hash+timestamp).encode("utf8"), vk)

        print(tree.current_groupid, len(self.request.body), self.request.body)

class UserHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_argument("user_id")
        timestamp = self.get_argument("timestamp")
        signature = self.get_argument("signature")

        vk = keys.UmbralPublicKey.from_bytes(bytes.fromhex(str(user_id)))
        sig = signing.Signature.from_bytes(bytes.fromhex(str(signature)))
        # vk = VerifyingKey.from_string(bytes.fromhex(str(user_id)), curve=NIST384p)
        assert sig.verify(timestamp.encode("utf8"), vk)
        # check database if this user located at current node
        # if not, query to get node id for the user
        # if not existing, query for the replicated

        # res = {"user_id": user_id}
        # user = database.connection.get("SELECT * FROM "+tree.current_port+"users WHERE user_id = %s ORDER BY replication_id ASC LIMIT 1", user_id)
        # if user:
        #     res["user"] = user
        # else:
        #     user_bin = bin(int(user_id[2:], 16))[2:].zfill(64*4)
        #     print(tree.current_port, user_id[2:], user_bin)

        #     groupids = tree.node_neighborhoods.keys()
        #     distance = 0
        #     for i in groupids:
        #         new_distance = tree.group_distance(i, user_bin)
        #         if new_distance < distance or not distance:
        #             distance = new_distance 
        #             groupid = i
        #     print(tree.current_port, tree.current_groupid, group_id, distance)
        #     res["node"] = [groupid, tree.node_neighborhoods[group_id]]
        longest = miner.longest_chain() or []
        for block in longest:
            data = json.loads(block["data"])
            if data["user_id"] == user_id:
                self.finish(data)
                break
        else:
            self.finish({})

    def post(self):
        user_id = self.get_argument("user_id")
        folder_hash = self.get_argument("folder_hash")
        block_size = int(self.get_argument("block_size"))
        folder_size = int(self.get_argument("folder_size"))
        groupid = self.get_argument("groupid")
        capsule = self.get_argument("capsule")
        timestamp = self.get_argument("timestamp")
        signature = self.get_argument("signature")

        vk = keys.UmbralPublicKey.from_bytes(bytes.fromhex(str(user_id)))
        sig = signing.Signature.from_bytes(bytes.fromhex(str(signature)))
        assert sig.verify(timestamp.encode("utf8"), vk)

        print(tree.current_port, len(self.request.body))
        if not os.path.exists("data/%s" % user_id):
            os.mkdir("data/%s" % user_id)
        open("data/%s/%s" % (user_id, folder_hash), "wb").write(self.request.body)
        open("data/%s/%s_capsule" % (user_id, folder_hash), "wb").write(bytes.fromhex(capsule))

        data = {"folder_hash": folder_hash, "block_size":block_size, "folder_size": folder_size, "groupid": groupid, "user_id": user_id, "by": tree.current_port}
        tree.forward(["UPDATE_HOME", user_id, data, time.time(), uuid.uuid4().hex])
        self.finish()

def main():
    print(tree.current_port, "fs")
    mining_task = tornado.ioloop.PeriodicCallback(mining, 1000) # , jitter=0.5
    mining_task.start()

if __name__ == '__main__':
    # main()
    print("run python node.py pls")

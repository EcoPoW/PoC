from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid
import hashlib
import copy

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpclient
import tornado.gen

import torndb

import setting
import tree
import node


def longest_chain(root_hash = '0'*64):
    roots = setting.db.query("SELECT * FROM "+tree.current_port+"chain WHERE prev_hash = %s ORDER BY nonce", root_hash)

    chains = []
    prev_hashs = []
    for root in roots:
        chains.append([root.hash])
        prev_hashs.append(root.hash)

    while True:
        if prev_hashs:
            prev_hash = prev_hashs.pop(0)
        else:
            break

        leaves = setting.db.query("SELECT * FROM "+tree.current_port+"chain WHERE prev_hash = %s ORDER BY nonce", prev_hash)
        if len(leaves) > 0:
            for leaf in leaves:
                for c in chains:
                    if c[-1] == prev_hash:
                        chain = copy.copy(c)
                        chain.append(leaf.hash)
                        chains.append(chain)
                        break
                if leaf.hash not in prev_hashs and leaf.hash:
                    prev_hashs.append(leaf.hash)

    longest = None
    for i in chains:
        # print(i)
        if not longest:
            longest = i
        if len(longest) < len(i):
            longest = i
    return longest

certain_value = "0"
certain_value = certain_value + 'f'*(64-len(certain_value))

nonce = 0
def mining():
    global nonce

    longest = longest_chain()
    # print(longest)
    longest_hash = longest[-1] if longest else "0"*64

    block_hash = hashlib.sha256(('last.data' + longest_hash + str(tree.current_port) + str(nonce)).encode('utf8')).hexdigest()
    if block_hash < certain_value:
        print(nonce, block_hash)
        # db.execute("UPDATE chain SET hash = %s, prev_hash = %s, nonce = %s, wallet_address = %s WHERE id = %s", block_hash, longest_hash, nonce, wallet_address, last.id)
        # setting.db.execute("INSERT INTO "+tree.current_port+"chain (hash, prev_hash, nonce, wallet_address, data) VALUES (%s, %s, %s, %s, '')", block_hash, longest_hash, nonce, str(tree.current_port))

        message = ["NEW_BLOCK", block_hash, longest_hash, nonce, str(tree.current_port), time.time(), uuid.uuid4().hex]
        tree.forward(message)
        print(tree.current_port, "mining %s" % nonce, block_hash)
        nonce = 0

    nonce += 1

def new_block(seq):
    _, block_hash, longest_hash, nonce, wallet_address, timestamp, msg_id = seq
    setting.db.execute("INSERT INTO "+tree.current_port+"chain (hash, prev_hash, nonce, wallet_address, data) VALUES (%s, %s, %s, %s, '')", block_hash, longest_hash, nonce, wallet_address)

def main():
    print(tree.current_port, "miner")
    setting.db.execute("TRUNCATE "+tree.current_port+"chain")

    mining_task = tornado.ioloop.PeriodicCallback(mining, 1000) # , jitter=0.5
    mining_task.start()

if __name__ == '__main__':
    print("run python node.py pls")

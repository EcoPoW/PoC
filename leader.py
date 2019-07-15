from __future__ import print_function

import time
import uuid
import hashlib

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpclient
import tornado.gen
import tornado.escape

import setting
import tree
import node
import database

certain_value = "0"
certain_value = certain_value + 'f'*(64-len(certain_value))

working = False
current_view = None

root_jump = {}
def lastest_block(root_hash):
    global root_jump

    chains = []
    prev_hashs = []
    if root_hash in root_jump:
        recent_hash = root_jump[root_hash]
        chains.append([recent_hash])
        prev_hashs.append(recent_hash)

    else:
        roots = database.connection.query("SELECT * FROM graph"+tree.current_port+" WHERE from_block = %s OR to_block = %s ORDER BY nonce", root_hash, root_hash)

        for root in roots:
            # print(root.id)
            chains.append([root.hash])
            prev_hashs.append(root.hash)

    while True:
        if prev_hashs:
            prev_hash = prev_hashs.pop(0)
        else:
            break

        leaves = database.connection.query("SELECT * FROM graph"+tree.current_port+" WHERE from_block = %s AND sender = %s ORDER BY nonce", prev_hash, root_hash)
        if len(leaves) > 0:
            for leaf in leaves:
                # print(leaf.id)
                for c in chains:
                    if c[-1] == prev_hash:
                        chain = c.copy()
                        chain.append(leaf.hash)
                        chains.append(chain)
                        break
                if leaf.hash not in prev_hashs and leaf.hash:
                    prev_hashs.append(leaf.hash)

        leaves = database.connection.query("SELECT * FROM graph"+tree.current_port+" WHERE to_block = %s AND receiver = %s ORDER BY nonce", prev_hash, root_hash)
        if len(leaves) > 0:
            for leaf in leaves:
                # print(leaf.id)
                for c in chains:
                    if c[-1] == prev_hash:
                        chain = c.copy()
                        chain.append(leaf.hash)
                        chains.append(chain)
                        break
                if leaf.hash not in prev_hashs and leaf.hash:
                    prev_hashs.append(leaf.hash)

    longest = []
    for i in chains:
        if not longest:
            longest = i
        if len(longest) < len(i):
            longest = i
    # print(longest)
    if len(longest) > 3:
        root_jump[root_hash] = longest[-3]
    return longest


def forward(seq):
    # global processed_message_ids

    # msg_id = seq[-1]
    # if msg_id in processed_message_ids:
    #     return
    # processed_message_ids.add(msg_id)
    msg = tornado.escape.json_encode(seq)

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
        print(tree.current_port, "leader view", current_view)
        # self.remove_node = True
        # if False: #temp disable force disconnect
        #     print(tree.current_port, "leader force disconnect")
        #     self.remove_node = False
        #     self.close()
        #     return

        print(tree.current_port, "leader connected")
        if self not in LeaderHandler.leader_nodes:
            LeaderHandler.leader_nodes.add(self)

    def on_close(self):
        print(tree.current_port, "leader disconnected")
        if self in LeaderHandler.leader_nodes: # and self.remove_node
            LeaderHandler.leader_nodes.remove(self)
        # self.remove_node = True

    @tornado.gen.coroutine
    def on_message(self, msg):
        seq = tornado.escape.json_decode(msg)
        print(tree.current_port, "on message from leader connector", seq)

        if seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        # elif seq[0] == "TX":
        #     transaction = seq[1]
        #     txid = transaction["transaction"]["txid"]
        #     sender = transaction["transaction"]["sender"]
        #     receiver = transaction["transaction"]["receiver"]
        #     amount = transaction["transaction"]["amount"]
        #     timestamp = transaction["transaction"]["timestamp"]
        #     signature = transaction["signature"]
        #     nonce = transaction["nonce"]
        #     from_block = transaction["from_block"]
        #     to_block = transaction["to_block"]

        #     # sender_blocks = lastest_block(sender)
        #     # receiver_blocks = lastest_block(receiver)

        #     if from_block in locked_blocks or to_block in locked_blocks:
        #         message = ["NAK", txid]
        #         self.write_message(tornado.escape.json_encode(message))
        #     else:
        #         message = ["ACK", txid]
        #         self.write_message(tornado.escape.json_encode(message))
        #     print(tree.current_port, "TX", message)
        #     return

        # elif seq[0] == "ACK":
        #     txid = seq[1]
        #     reply = block_to_reply.get(txid)
        #     if self in reply:
        #         reply.remove(self)
        #     print(tree.current_port, "ACK reply", reply)
        #     if reply:
        #         return

        #     transaction = block_to_confirm.get(txid)
        #     sender = transaction["transaction"]["sender"]
        #     receiver = transaction["transaction"]["receiver"]

        #     block_hash = transaction["block_hash"]
        #     nonce = transaction["nonce"]
        #     from_block = transaction["from_block"]
        #     to_block = transaction["to_block"]
        #     return

        # elif seq[0] == "NAK":
        #     txid = seq[1]
        #     transaction = block_to_confirm.get(txid)
        #     if transaction:
        #         from_block = transaction["from_block"]
        #         to_block = transaction["to_block"]

        #         if from_block in locked_blocks:
        #             locked_blocks.remove(from_block)
        #         if to_block in locked_blocks:
        #             locked_blocks.remove(to_block)
        #         if transaction:
        #             del block_to_confirm[txid]
        #     return

        elif seq[0] == "PBFT-O":
            pass
        elif seq[0] == "PBFT-P":
            pass
        elif seq[0] == "PBFT-C":
            pass
        elif seq[0] == "PBFT-V":
            pass

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
        self.remove_node = False
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 1000.0)

    def close(self):
        self.remove_node = True
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
            print(tree.current_port, "reconnect leader on connect ...")
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)


    def on_message(self, msg):
        if msg is None:
            if not self.remove_node:
                print(tree.current_port, "reconnect leader on message...")
                # self.ws_uri = "ws://%s:%s/leader?host=%s&port=%s" % (self.host, self.port, tree.current_host, tree.current_port)
                tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = tornado.escape.json_decode(msg)
        print(tree.current_port, "on message from leader", seq)

        if seq[0] == "NEW_BLOCK":
            miner.new_block(seq)

        # elif seq[0] == "TX":
        #     transaction = seq[1]
        #     txid = transaction["transaction"]["txid"]
        #     sender = transaction["transaction"]["sender"]
        #     receiver = transaction["transaction"]["receiver"]
        #     amount = transaction["transaction"]["amount"]
        #     timestamp = transaction["transaction"]["timestamp"]
        #     signature = transaction["signature"]
        #     nonce = transaction["nonce"]
        #     from_block = transaction["from_block"]
        #     to_block = transaction["to_block"]

        #     # sender_blocks = lastest_block(sender)
        #     # receiver_blocks = lastest_block(receiver)

        #     if from_block in locked_blocks or to_block in locked_blocks:
        #         message = ["NAK", txid]
        #         self.conn.write_message(tornado.escape.json_encode(message))
        #     else:
        #         message = ["ACK", txid]
        #         self.conn.write_message(tornado.escape.json_encode(message))
        #     print(tree.current_port, "TX", message)
        #     return

        # elif seq[0] == "ACK":
        #     txid = seq[1]
        #     reply = block_to_reply.get(txid)
        #     if self in reply:
        #         reply.remove(self)
        #     print(tree.current_port, "ACK reply", reply)
        #     if reply:
        #         return

        #     transaction = block_to_confirm.get(txid)
        #     sender = transaction["transaction"]["sender"]
        #     receiver = transaction["transaction"]["receiver"]

        #     block_hash = transaction["block_hash"]
        #     nonce = transaction["nonce"]
        #     from_block = transaction["from_block"]
        #     to_block = transaction["to_block"]
        #     data = {}
        #     database.connection.execute("INSERT INTO graph"+tree.current_port+" (hash, from_block, to_block, sender, receiver, nonce, data) VALUES (%s, %s, %s, %s, %s, %s, %s)", block_hash, from_block, to_block, sender, receiver, nonce, tornado.escape.json_encode(data))
        #     return

        # elif seq[0] == "NAK":
        #     txid = seq[1]
        #     transaction = block_to_confirm.get(txid)
        #     if transaction:
        #         from_block = transaction["from_block"]
        #         to_block = transaction["to_block"]

        #         if from_block in locked_blocks:
        #             locked_blocks.remove(from_block)
        #         if to_block in locked_blocks:
        #             locked_blocks.remove(to_block)
        #         if transaction:
        #             del block_to_confirm[txid]
        #     return

        # else:
        forward(seq)

transactions = []
locked_blocks = set()
block_to_confirm = {}
block_to_reply = {}
def mining():
    # global working
    # global transactions
    # global locked_blocks
    if transactions:
        seq = transactions.pop(0)
        transaction = seq[1]
        txid = transaction["transaction"]["txid"]
        sender = transaction["transaction"]["sender"]
        receiver = transaction["transaction"]["receiver"]
        amount = transaction["transaction"]["amount"]
        timestamp = transaction["transaction"]["timestamp"]
        signature = transaction["signature"]
        print(tree.current_port, "leader view", current_view)

        sender_blocks = lastest_block(sender)
        receiver_blocks = lastest_block(receiver)

        from_block = sender_blocks[-1] if sender_blocks else sender
        to_block = receiver_blocks[-1] if receiver_blocks else receiver
        # if from_block in locked_blocks or to_block in locked_blocks:
        #     transactions.append(seq)
        #     tornado.ioloop.IOLoop.instance().call_later(1, mining)
        #     return

        nonce = 0
        data = txid + sender + receiver + str(amount) + str(timestamp) + signature + from_block + to_block + str(tree.current_port)
        while True:
            block_hash = hashlib.sha256((data + str(nonce)).encode('utf8')).hexdigest()
            if block_hash < certain_value:
                locked_blocks.add(from_block)
                locked_blocks.add(to_block)
                transaction["block_hash"] = block_hash
                transaction["nonce"] = nonce
                transaction["from_block"] = from_block
                transaction["to_block"] = to_block
                block_to_confirm[txid] = transaction

                reply = block_to_reply.setdefault(txid, set())
                for leader_node in LeaderHandler.leader_nodes:
                    reply.add(leader_node)

                for leader_connector in LeaderConnector.leader_nodes:
                    reply.add(leader_connector)
                # print(tree.current_port, "reply", reply)

                message = ["NEW_TX_BLOCK", transaction, time.time(), uuid.uuid4().hex]
                print(tree.current_port, message)
                tree.forward(message)

                message = ["TX", transaction]
                # forward(message)
                break

            nonce += 1

        print(tree.current_port, txid, from_block, to_block)

    if working:
        tornado.ioloop.IOLoop.instance().call_later(1, mining)


current_leaders = set()
previous_leaders = set()
def update(leaders):
    global current_leaders
    global previous_leaders
    global working

    current_leaders = leaders
    if ("localhost", tree.current_port) in leaders - previous_leaders:
        for other_leader_addr in leaders:
            connected = set([(i.host, i.port) for i in LeaderConnector.leader_nodes]) |\
                        set([(i.from_host, i.from_port) for i in LeaderHandler.leader_nodes]) |\
                        set([(tree.current_host, tree.current_port)])
            if other_leader_addr not in connected:
                # print(tree.current_port, other_leader_addr, connected)
                LeaderConnector(*other_leader_addr)

                if not working:
                    tornado.ioloop.IOLoop.instance().add_callback(mining)
                working = True

    nodes_to_close = set()
    for node in LeaderConnector.leader_nodes:
        if (node.host, node.port) not in leaders:
            nodes_to_close.add(node)

    # print(tree.current_port, "nodes_to_close", len(nodes_to_close))
    while nodes_to_close:
        nodes_to_close.pop().close()


    if ("localhost", tree.current_port) not in leaders:
        working = False

        while LeaderConnector.leader_nodes:
            LeaderConnector.leader_nodes.pop().close()

    previous_leaders = leaders


if __name__ == '__main__':
    # main()
    print("run python node.py pls")

from __future__ import print_function

import os
import subprocess
import time
import socket
import argparse
import random
import uuid
import base64
import hashlib
import urllib

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen
import tornado.escape

# from ecdsa import SigningKey, NIST384p
from umbral import pre, keys, signing
import umbral.config

incremental_port = 8000

@tornado.gen.coroutine
def get_group(target):
    known_addresses_list = list(ControlHandler.known_addresses)
    addr = random.choice(known_addresses_list)
    http_client = tornado.httpclient.AsyncHTTPClient()
    while True:
        url = "http://%s:%s/get_group?groupid=%s" % (tuple(addr)+(target,))
        try:
            response = yield http_client.fetch(url)#, method="POST", body=tornado.escape.json_encode(data)
        except Exception as e:
            print("Error: %s" % e)
        print(addr, response.body)
        res = tornado.escape.json_decode(response.body)
        if res["groupid"] == res["current_groupid"]:
            break
        addr = res["address"][0]
    return addr, res["groupid"]

class Application(tornado.web.Application):
    def __init__(self):
        settings = {
            "debug":True,
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
        }
        handlers = [(r"/control", ControlHandler),
                    (r"/new_node", NewNodeHandler),
                    (r"/new_tx", NewTxHandler),
                    (r"/dashboard", DashboardHandler),
                    (r"/get_user", GetUserHandler),
                    (r"/new_user", NewUserHandler),
                    (r"/new_file", NewFileHandler),
                    (r"/visualize", VisualizeHandler),
                    (r"/visualize_data", VisualizeDataHandler),
                    (r"/static/(.*)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
                    ]

        tornado.web.Application.__init__(self, handlers, **settings)

class NewNodeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.count = int(self.get_argument("n", "1"))
        tornado.ioloop.IOLoop.instance().call_later(1, self.add)

    def add(self):
        global incremental_port
        if self.count <= 0:
            self.finish()
            return
        self.count -= 1
        incremental_port += 1
        subprocess.Popen(["python3", "node.py", "--port=%s"%incremental_port, "--control_port=8000"], shell=False)
        self.write("new node %s\n" % incremental_port)
        tornado.ioloop.IOLoop.instance().call_later(2, self.add)

class NewTxHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        USER_NO = 4
        count = int(self.get_argument("n", "1"))
        for i in range(count):
            user_nos = list(range(USER_NO))
            i = random.choice(user_nos)
            sender_filename = "pk" + str(i)
            sender_sk = keys.UmbralPrivateKey.from_bytes(bytes.fromhex(open("data/pk/"+sender_filename).read()))
            sender_vk = sender_sk.get_pubkey()
            sender = sender_vk.to_bytes().hex()

            user_nos.remove(i)
            j = random.choice(user_nos)
            receiver_filename = "pk" + str(j)
            receiver_sk = keys.UmbralPrivateKey.from_bytes(bytes.fromhex(open("data/pk/"+receiver_filename).read()))
            amount = random.randint(1, 20)
            receiver_vk = receiver_sk.get_pubkey()
            receiver = receiver_vk.to_bytes().hex()

            txid = uuid.uuid4().hex
            timestamp = int(time.time())
            transaction = {
                "txid": txid,
                "sender": sender,
                "receiver": receiver,
                "timestamp": timestamp,
                "amount": amount
            }
            # print(transaction)
            sender_sign = signing.Signer(sender_sk)
            signature = sender_sign(str(timestamp).encode("utf8"))
            data = {
                "transaction": transaction,
                "signature": bytes(signature).hex()
            }

            assert signature.verify(str(timestamp).encode("utf8"), sender_vk)

            known_addresses_list = list(ControlHandler.known_addresses)
            addr = random.choice(known_addresses_list)

            self.write("%s %s\n" % addr)
            http_client = tornado.httpclient.AsyncHTTPClient()
            try:
                response = yield http_client.fetch("http://%s:%s/new_tx" % tuple(addr), method="POST", body=tornado.escape.json_encode(data))
            except Exception as e:
                print("Error: %s" % e)
            # result = tornado.escape.json_decode(response.body)
            # branches = result["available_branches"]

            self.write("%s\n" % response.body)
            # self.write("new tx %s\n" % txid)
        self.finish()


class GetUserHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        sk_filename = "pk1"
        sk = keys.UmbralPrivateKey.from_bytes(bytes.fromhex(open("data/pk/"+sk_filename).read()))
        vk = sk.get_pubkey()
        user_id = vk.to_bytes().hex()
        # sender_binary = bin(int(vk.to_bytes().hex(), 16))#[2:].zfill(768)
        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign(str(timestamp).encode("utf8"))
        assert signature.verify(str(timestamp).encode("utf8"), vk)

        known_addresses_list = list(ControlHandler.known_addresses)
        addr = random.choice(known_addresses_list)
        http_client = tornado.httpclient.AsyncHTTPClient()
        print(len(vk.to_bytes().hex()), vk.to_bytes().hex())
        # print(len(bin(int(vk.to_bytes().hex(), 16))), bin(int(vk.to_bytes().hex(), 16)))
        print(len(bytes(signature).hex()), bytes(signature).hex())
        url = "http://%s:%s/user?user_id=%s&timestamp=%s&signature=%s" % (tuple(addr)+(user_id, str(timestamp), bytes(signature).hex()))
        # print(url)
        try:
            response = yield http_client.fetch(url)#, method="POST", body=tornado.escape.json_encode(data)
        except Exception as e:
            print("Error: %s" % e)

        self.finish(tornado.escape.json_decode(response.body))

class NewUserHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        sk_filename = "pk1"
        sk = keys.UmbralPrivateKey.gen_key()
        open("data/pk/"+sk_filename, "w").write(sk.to_bytes().hex())
        vk = sk.get_pubkey()
        user_id = vk.to_bytes().hex()
        timestamp = str(time.time())
        sk_sign = signing.Signer(sk)
        signature = sk_sign(timestamp.encode("utf8"))

        content = b"{}"
        ciphertext, capsule = pre.encrypt(vk, content)
        folder_size = "0"
        block_size = len(ciphertext)
        folder_hash = hashlib.sha1(ciphertext).hexdigest()
        folder_hash_binary = bin(int(folder_hash, 16))[2:].zfill(32*4)
        addr, groupid = yield get_group(folder_hash_binary)
        print("ciphertext", len(ciphertext), "capsule", capsule.to_bytes().hex())

        http_client = tornado.httpclient.AsyncHTTPClient()
        url = "http://%s:%s/user?user_id=%s&folder_hash=%s&block_size=%s&folder_size=%s&groupid=%s&capsule=%s&timestamp=%s&signature=%s" \
                % (tuple(addr)+(user_id, folder_hash, block_size, folder_size, groupid, capsule.to_bytes().hex(), timestamp, bytes(signature).hex()))
        try:
            response = yield http_client.fetch(url, method="POST", body=ciphertext)
        except Exception as e:
            print("Error: %s" % e)

        self.finish({"user_id":user_id})

class NewFileHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        sk_filename = "pk1"
        sk = keys.UmbralPrivateKey.from_bytes(bytes.fromhex(open("data/pk/"+sk_filename).read()))
        vk = sk.get_pubkey()
        user_id = vk.to_bytes().hex()
        http_client = tornado.httpclient.AsyncHTTPClient()

        # get root tree hash from blockchain, from random node
        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign(str(timestamp).encode("utf8"))
        assert signature.verify(str(timestamp).encode("utf8"), vk)

        known_addresses_list = list(ControlHandler.known_addresses)
        addr = random.choice(known_addresses_list)
        # print(len(vk.to_bytes().hex()), vk.to_bytes().hex())
        # print(len(bytes(signature).hex()), bytes(signature).hex())
        url = "http://%s:%s/user?user_id=%s&timestamp=%s&signature=%s" % (tuple(addr)+(user_id, str(timestamp), bytes(signature).hex()))
        try:
            response = yield http_client.fetch(url)#, method="POST", body=tornado.escape.json_encode(data)
            user = tornado.escape.json_decode(response.body)
            # print(user)
            groupid = user["groupid"]
            folder_hash = user["folder_hash"]
        except Exception as e:
            print("Error: %s" % e)

        # get content object and capsule from the group
        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign((str(folder_hash)+str(timestamp)).encode("utf8"))
        assert signature.verify((str(folder_hash)+str(timestamp)).encode("utf8"), vk)

        addr, _ = yield get_group(groupid)
        print(_, groupid)
        url = "http://%s:%s/object?hash=%s&user_id=%s&timestamp=%s&signature=%s" % (tuple(addr)+(folder_hash, user_id, str(timestamp), bytes(signature).hex()))
        response = yield http_client.fetch(url)
        ciphertext = response.body

        url = "http://%s:%s/capsule?hash=%s&user_id=%s&timestamp=%s&signature=%s" % (tuple(addr)+(folder_hash, user_id, str(timestamp), bytes(signature).hex()))
        response = yield http_client.fetch(url)
        capsule = response.body

        # decode
        print(ciphertext, capsule)
        cleartext = pre.decrypt(ciphertext=ciphertext,
                                capsule=pre.Capsule.from_bytes(capsule, umbral.config.default_params()),
                                decrypting_key=sk)

        # put file
        content = open("data/pk/"+sk_filename, "rb").read()
        ciphertext, capsule = pre.encrypt(vk, content)
        print(len(ciphertext), capsule.to_bytes())
        sha1 = hashlib.sha1(ciphertext).hexdigest()
        sha1_binary = bin(int(sha1, 16))[2:].zfill(32*4)
        print(sha1_binary, len(sha1_binary), sha1, 16)
        addr, groupid = yield get_group(sha1_binary)

        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign((str(sha1)+str(timestamp)).encode("utf8"))
        assert signature.verify((str(sha1)+str(timestamp)).encode("utf8"), vk)

        url = "http://%s:%s/object?hash=%s&user_id=%s&timestamp=%s&signature=%s" % (tuple(addr)+(sha1, user_id, str(timestamp), bytes(signature).hex()))
        http_client = tornado.httpclient.AsyncHTTPClient()
        response = yield http_client.fetch(url, method="POST", body=ciphertext)
        print(len(ciphertext), ciphertext)

        # update
        data = tornado.escape.json_decode(cleartext)
        data["filename"] = [sha1, len(ciphertext), groupid, time.time()]

        # encode
        content = tornado.escape.json_encode(data).encode("utf8")
        ciphertext, capsule = pre.encrypt(vk, content)
        folder_size = str(len(ciphertext))
        block_size = len(ciphertext)
        folder_hash = hashlib.sha1(ciphertext).hexdigest()
        folder_hash_binary = bin(int(folder_hash, 16))[2:].zfill(32*4)
        addr, groupid = yield get_group(folder_hash_binary)
        print("ciphertext", len(ciphertext), "capsule", capsule.to_bytes().hex())

        # put
        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign(str(timestamp).encode("utf8"))
        assert signature.verify(str(timestamp).encode("utf8"), vk)

        url = "http://%s:%s/user?user_id=%s&folder_hash=%s&block_size=%s&folder_size=%s&groupid=%s&capsule=%s&timestamp=%s&signature=%s" \
                % (tuple(addr)+(user_id, folder_hash, block_size, folder_size, groupid, capsule.to_bytes().hex(), timestamp, bytes(signature).hex()))
        try:
            response = yield http_client.fetch(url, method="POST", body=ciphertext)
        except Exception as e:
            print("Error: %s" % e)


class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("")
        self.finish()

class ControlHandler(tornado.websocket.WebSocketHandler):
    known_addresses = dict()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        print("control: node connected")
        # print("Clients", len(ControlHandler.known_addresses))
        self.addr = None

    def on_close(self):
        print("control: node disconnected")
        if self.addr in ControlHandler.known_addresses:
            del ControlHandler.known_addresses[self.addr]

    # def send_to_client(self, msg):
    #     print("send message: %s" % msg)
    #     self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        seq = tornado.escape.json_decode(msg)
        print("control on message", seq)
        if seq[0] == "ADDRESS":
            self.addr = tuple(seq[1:3])
            # print(self.addr)
            known_addresses_list = list(ControlHandler.known_addresses)
            random.shuffle(known_addresses_list)
            # known_addresses_list.sort(key=lambda l:int(l[1]))
            self.write_message(tornado.escape.json_encode(["BOOTSTRAP_ADDRESS", known_addresses_list[:3]]))
            ControlHandler.known_addresses[self.addr] = self
            # print(ControlHandler.known_addresses)
        elif seq[0] == "ADDRESS2":
            pass

        for w in VisualizeDataHandler.waiters:
            w.write_message(msg)


class VisualizeHandler(tornado.web.RequestHandler):
    def get(self):
        # global control_node
        self.messages = VisualizeDataHandler.cache
        self.render("index.html")


class VisualizeDataHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def open(self):
        # print ("new client opened")
        VisualizeDataHandler.waiters.add(self)

    def on_close(self):
        VisualizeDataHandler.waiters.remove(self)

    @classmethod
    def update_cache(cls, msg):
        cls.cache.append(msg)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, msg):
        print("sending message to waiters", len(cls.waiters))
        # logging.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(msg)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        # logging.info("got message %r", message)
        print("got message ", message)
        # self.write("<br>current_groupid: %s <br>" % message)
        VisualizeDataHandler.send_updates(message)


def main():
    global port, control_port

    parser = argparse.ArgumentParser(description="control description")
    parser.add_argument('--control_port', default=8000)

    args = parser.parse_args()
    control_port = args.control_port

    server = Application()
    server.listen(control_port)
    # tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

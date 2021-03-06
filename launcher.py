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

incremental_port = 8000

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
                    (r"/static/(.*)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
                    ]

        tornado.web.Application.__init__(self, handlers, **settings)

class NewNodeHandler(tornado.web.RequestHandler):
    def get(self):
        global incremental_port
        count = int(self.get_argument("n", "1"))
        for i in range(count):
            incremental_port += 1
            subprocess.Popen(["python3", "node.py", "--port=%s"%incremental_port, "--control_port=8000"])
            self.write("new node %s\n" % incremental_port)
        self.finish()

class NewTxHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        count = int(self.get_argument("n", "1"))
        USER_NO = 4
        for i in range(count):
            i = random.randint(1, USER_NO)
            # sk_filename = sys.argv[1]
            sk_filename = "p" + str(i) + ".pem"
            sk = SigningKey.from_pem(open("data/pk/"+sk_filename).read())

            j = i
            while j == i:
                j = random.randint(1, USER_NO)
            receiver_filename = "p" + str(j) + ".pem"
            rec = SigningKey.from_pem(open("data/pk/"+receiver_filename).read())
            amount = random.randint(1, 20)

            vk = sk.get_verifying_key()
            sender = base64.b64encode(vk.to_string())
            receiver_key = rec.get_verifying_key()
            receiver = base64.b64encode(receiver_key.to_string())
            txid = uuid.uuid4().hex
            timestamp = time.time()

            transaction = {
                "txid": txid,
                "sender": str(sender, encoding="utf-8"),
                "receiver":str(receiver, encoding="utf-8"),
                "timestamp": timestamp,
                "amount": amount
            }
            print(transaction)
            signature = sk.sign(tornado.escape.json_encode(transaction).encode('utf-8'))
            data = {
                "transaction": transaction,
                "signature": str(base64.b64encode(signature), encoding="utf-8")
            }

            assert vk.verify(signature, tornado.escape.json_encode(transaction).encode('utf-8'))

            known_addresses_list = list(ControlHandler.known_addresses)
            addr = random.choice(known_addresses_list)
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
        sender_binary = bin(int(vk.to_bytes().hex(), 16))#[2:].zfill(768)
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
        url = "http://%s:%s/user?user_id=%s&signature=%s&timestamp=%s" % (tuple(addr)+(vk.to_bytes().hex(), bytes(signature).hex(), str(timestamp)))
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
        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign(str(timestamp).encode("utf8"))

        known_addresses_list = list(ControlHandler.known_addresses)
        addr = random.choice(known_addresses_list)
        http_client = tornado.httpclient.AsyncHTTPClient()
        # print(len(vk.to_bytes().hex()), vk.to_bytes().hex())
        # print(len(bytes(signature).hex()), bytes(signature).hex())
        url = "http://%s:%s/user?user_id=%s&signature=%s&timestamp=%s" % (tuple(addr)+(user_id, bytes(signature).hex(), str(timestamp)))
        # print(url)
        try:
            response = yield http_client.fetch(url)#, method="POST", body=tornado.escape.json_encode(data)
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

        content = open("data/pk/"+sk_filename, "rb").read()
        ciphertext, capsule = pre.encrypt(vk, content)
        print(len(ciphertext), capsule.to_bytes())
        sha1 = hashlib.sha1(ciphertext).hexdigest()
        sha1_binary = bin(int(sha1, 16))[2:].zfill(32*4)
        print(sha1_binary, len(sha1_binary), sha1, 16)

        timestamp = time.time()
        sk_sign = signing.Signer(sk)
        signature = sk_sign((str(sha1)+str(timestamp)).encode("utf8"))
        assert signature.verify((str(sha1)+str(timestamp)).encode("utf8"), vk)

        known_addresses_list = list(ControlHandler.known_addresses)
        addr = random.choice(known_addresses_list)
        http_client = tornado.httpclient.AsyncHTTPClient()
        # print(len(vk.to_bytes().hex()), vk.to_bytes().hex())
        # # print(len(bin(int(vk.to_bytes().hex(), 16))), bin(int(vk.to_bytes().hex(), 16)))
        # print(len(bytes(signature).hex()), bytes(signature).hex())
        while True:
            url = "http://%s:%s/get_group?groupid=%s" % (tuple(addr)+(sha1_binary,))
            try:
                response = yield http_client.fetch(url)#, method="POST", body=tornado.escape.json_encode(data)
            except Exception as e:
                print("Error: %s" % e)
            print(addr, response.body)
            res = tornado.escape.json_decode(response.body)
            if res["groupid"] == res["current_groupid"]:
                break
            addr = res["address"][0]

        url = "http://%s:%s/object?hash=%s&user_id=%s&timestamp=%s&signature=%s" % (tuple(addr)+(sha1, user_id, str(timestamp), bytes(signature).hex()))
        print(url)
        response = yield http_client.fetch(url, method="POST", body=ciphertext)
        print(len(ciphertext), ciphertext)

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
        if seq[0] == u"ADDRESS":
            self.addr = tuple(seq[1:3])
            # print(self.addr)
            known_addresses_list = list(ControlHandler.known_addresses)
            random.shuffle(known_addresses_list)
            # known_addresses_list.sort(key=lambda l:int(l[1]))
            self.write_message(tornado.escape.json_encode(["BOOTSTRAP_ADDRESS", known_addresses_list[:3]]))
            ControlHandler.known_addresses[self.addr] = self
            # print(ControlHandler.known_addresses)
        elif seq[0]:
            pass


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

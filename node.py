import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
from tornado.httpserver import HTTPServer
import time
import socket
import subprocess

from tornado import gen
from tornado.websocket import websocket_connect
from multiprocessing import Process,Pool,Queue,Manager
import pickle

@gen.coroutine
def read(to_url):
    print("client trying to read msg")
    webSocket = yield websocket_connect(to_url)
    msg = yield webSocket.read_message()
            
@gen.coroutine
def write(to_url,msg,msgId):
    def callback():
        print("Hello World")
        self.finish()
    
    print("client trying to write msg")
    print(to_url)
    print(msg)
    webSocket = yield websocket_connect(to_url)
    webSocket.write_message(msg+";;;"+str(msgId),callback)


def open_server(port):
    server = application()
    server.listen(port)  # 比较一下listen和bind的区别
    tornado.ioloop.IOLoop.instance().start()


served_msg=[]

class application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", main_handler),
                    ]
        settings = dict(debug=True)
        print("port " + str(port1) + " server starts")

        tornado.web.Application.__init__(self, handlers, **settings)


class main_handler(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        print("data received")

    clients = set()


    def check_origin(self, origin):
        return True


    def open(self):
        print(" A client connected."+port1)
        if self in main_handler.clients:
            print("dsafadf")
        main_handler.clients.add(self)

        print(len(main_handler.clients))

    def on_close(self):
        print("A client disconnected")
        main_handler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    @gen.coroutine
    def on_message(self, message):
        print("On Message"+str(message))
        
        if str(message).split(";;;")[1] in served_msg:
            print("message served")
            return
        print(str(message).split(";;;")[0]+":server")
        print("client number "+str(len(main_handler.clients)))

        # for c in main_handler.clients:
        #     if c!=self:
        #         c.write_message(message)
        with open(port1, 'rb') as f:
            tree=pickle.load(f)
        if len(tree[port1]) == 0:
            return
        for url in tree[port1]:
            to_url = "ws://localhost:" + url
            webSocket = yield websocket_connect(to_url)
            webSocket.write_message(str(message).split(";;;")[0]+";;;"+str(message).split(";;;")[1])

        # if len(peer) == 0:
        #     return
        # for u in peer.split(","):
        #     if u == str(port):
        #         return
        #     to_url = "ws://localhost:" + u
        #     webSocket = yield websocket_connect(to_url)
        #     webSocket.write_message(message.split(";;;")[0]+";;;"+message.split(";;;")[1])

        served_msg.append(str(message).split(";;;")[1])




import argparse

parser = argparse.ArgumentParser(description="program description")

parser.add_argument('--port1')
parser.add_argument('--port2')
parser.add_argument('--operation')
parser.add_argument('--message')

args = parser.parse_args()

port1 = args.port1
port2 = args.port2
operation=args.operation
message = args.message


pool=Pool(8)
    

if operation == "0":
    # pool.apply_async(open_server,(port1,))
    open_server(port1)


if operation == "1":
    to_url = "ws://localhost:" + args.port2
    print(to_url)
    # pool.apply_async(write,(to_url,message,1,))
    write(to_url,message,1)
    tornado.ioloop.IOLoop.instance().start()

if operation == "2":
    with open(port1, 'rb') as f:
        tree=pickle.load(f)
    if len(tree[port1]) != 0:
        for url in tree[port1]:
            to_url = "ws://localhost:" + url
            write(to_url,message,1)
        tornado.ioloop.IOLoop.instance().start()
        # tree=json.loads('{"3001": ",3002,3003", "3002": "3001,3004,3005", "3003": "3001,3006,3007", "3004": "3002,,", "3005": "3002,,", "3006": "3003,,", "3007": "3003,,"}')

        # tree=json.loads(f.read().replace('\n', ''))
        
        # print(tree)




    



# read("ws://localhost:8080")











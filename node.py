import time
import socket
import subprocess
import argparse

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen


# @tornado.gen.coroutine
# def read(to_url):
#     print("client trying to read msg")
#     webSocket = yield tornado.websocket.websocket_connect(to_url)
#     msg = yield webSocket.read_message()
            
# @tornado.gen.coroutine
# def write(to_url, msg, msg_id):
#     def callback():
#         print("Hello World")
#         self.finish()
    
#     print("client trying to write msg")
#     print(to_url)
#     print(msg)
#     webSocket = yield tornado.websocket.websocket_connect(to_url)
#     webSocket.write_message(msg+";;;"+str(msgId),callback)


served_msg = []

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", NodeHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class NodeHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    # def data_received(self, chunk):
    #     print("data received")

    def check_origin(self, origin):
        return True

    def open(self):
        # print(" A client connected."+port)
        if self in NodeHandler.clients:
            print("dsafadf")
        else:
            NodeHandler.clients.add(self)

        print(len(NodeHandler.clients))

    def on_close(self):
        print("A client disconnected")
        if self in NodeHandler.clients:
            NodeHandler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    @tornado.gen.coroutine
    def on_message(self, msg):
        print("On Message"+str(msg))
        
        if str(msg).split(";;;")[1] in served_msg:
            print("message served")
            return
        # print(str(msg).split(";;;")[0]+":server")
        print("client number "+str(len(NodeHandler.clients)))

        # for c in main_handler.clients:
        #     if c!=self:
        #         c.write_message(message)
        # with open(port, 'rb') as f:
        #     tree=pickle.load(f)
        # if len(tree[port]) == 0:
        #     return
        # for url in tree[port]:
        #     to_url = "ws://localhost:" + url
        #     webSocket = yield tornado.websocket.websocket_connect(to_url)
        #     webSocket.write_message(str(msg).split(";;;")[0]+";;;"+str(msg).split(";;;")[1])

        # if len(peer) == 0:
        #     return
        # for u in peer.split(","):
        #     if u == str(port):
        #         return
        #     to_url = "ws://localhost:" + u
        #     webSocket = yield tornado.websocket.websocket_connect(to_url)
        #     webSocket.write_message(message.split(";;;")[0]+";;;"+message.split(";;;")[1])

        served_msg.append(str(msg).split(";;;")[1])

control_node = None
def on_connect(future):
    global control_node
    print("on_connect")

    try:
        control_node = future.result()
        # for future, message in self.connect_waiting:
        #     self.waiting_inqueue(future)
        #     self.conn.write_message(message)
        # self.connect_waiting = []
    except:
        print("reconnect ...")
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

def on_message(msg):
    print("on_message", msg)

def connect():
    print("connect", control_port)
    tornado.websocket.websocket_connect("ws://localhost:%s/control" % control_port, callback=on_connect, on_message_callback=on_message)
    # if control_node:
    print(control_node)
    # tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

def main():
    global port, control_port

    parser = argparse.ArgumentParser(description="program description")
    parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    port = args.port
    control_port = args.control_port

    server = Application()
    server.listen(port)
    tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


    # if operation == "1":
    #     to_url = "ws://localhost:" + args.port2
    #     print(to_url)
    #     # pool.apply_async(write,(to_url,message,1,))
    #     write(to_url,message,1)
    #     tornado.ioloop.IOLoop.instance().start()

    # if operation == "2":
    #     with open(port, 'rb') as f:
    #         tree=pickle.load(f)
    #     if len(tree[port]) != 0:
    #         for url in tree[port]:
    #             to_url = "ws://localhost:" + url
    #             write(to_url,message,1)
    #         tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

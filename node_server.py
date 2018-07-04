import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options

from tornado import gen
from tornado.websocket import websocket_connect

served_msg=[]

class application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", main_handler),
                    ]
        settings = dict(debug=True)
        print("port " + str(port) + " server starts")

        tornado.web.Application.__init__(self, handlers, **settings)


class main_handler(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    clients = set()

    def check_origin(self, origin):
        return True


    def open(self):
        print(" A client connected."+port)
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
        if message.split(";;;")[1] in served_msg:
            print("message served")
            return
        print(message.split(";;;")[0]+":server")
        print("client number "+str(len(main_handler.clients)))

        # for c in main_handler.clients:
        #     if c!=self:
        #         c.write_message(message)
        
        if len(peer) == 0:
            return
        for u in peer.split(","):
            if u == str(port):
                return
            to_url = "ws://localhost:" + u
            webSocket = yield websocket_connect(to_url)
            webSocket.write_message(message.split(";;;")[0]+";;;"+message.split(";;;")[1])

        served_msg.append(message.split(";;;")[1])

import argparse

parser = argparse.ArgumentParser(description="program description")

parser.add_argument('--port')
parser.add_argument('--peer')
parser.add_argument('--url')

args = parser.parse_args()
port = args.port
peer = args.peer
url = args.url

server = application()
server.listen(port)  # 比较一下listen和bind的区别
tornado.ioloop.IOLoop.instance().start()

# port=8080
# server=application()
# server.listen(8080)
# tornado.ioloop.IOLoop.instance().start()












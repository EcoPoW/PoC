import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options

from tornado import gen
from tornado.websocket import websocket_connect


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
        print(" A client connected.")
        main_handler.clients.add(self)

        print(len(main_handler.clients))

    def on_close(self):
        print("A client disconnected")
        main_handler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    def on_message(self, message):
        print(message)
        for c in main_handler.clients:
            if c != self:
                c.write_message(message)


@gen.coroutine
def read(to_url):
    print("client trying to read msg")
    webSocket = yield websocket_connect(to_url)
    while True:

        msg = yield webSocket.read_message()
        if msg is None:
            break
        else:
            print(msg)
            
@gen.coroutine
def write(to_url,msg):
    print("client trying to write msg")
    webSocket = yield websocket_connect(to_url)
    webSocket.write_message(msg)



import argparse

parser = argparse.ArgumentParser(description="program description")

parser.add_argument('--port')
parser.add_argument('--end')
parser.add_argument('--url')

args = parser.parse_args()
port = args.port
end = args.end
url = args.url

# print(str(port) + " " + str(end))


if url != "0":
    to_url = "ws://localhost:" + url
    print(to_url)
    read(to_url)

else:

    server = application()
    server.listen(port)  # 比较一下listen和bind的区别

if end == "1":
    tornado.ioloop.IOLoop.instance().start()

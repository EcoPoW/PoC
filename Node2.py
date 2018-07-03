import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import websocket_connect
from tornado.options import define, options
import threading
import time
from multiprocessing import Process, Pool, Queue, Manager

define("port", default=8080, help="run on the given port", type=int)


class server_thread(threading.Thread):
    def __init__(self, port, peer_ports):
        threading.Thread.__init__(self)
        self.node = Node(port, peer_ports)

    def run(self):
        print("open server")
        self.node.open_server()


def ser(port):
    server = Application()
    server.listen(port)
    server.ioloop.start()


class Node:

    def __init__(self, port, peer_ports):
        self.port = port
        self.peer_ports = peer_ports

    def open_server(self):
        print("self port: " + str(self.port) + " server is online")
        server = Application()
        server.listen(self.port)
        # server.ioloop.start()

    def read_client(self, other_port):
        print("self port: " + str(self.port) + " reads msg from other port: " + str(other_port))
        to_url = "ws://localhost:" + str(other_port)
        client = Client(5, self.port)
        client.read(to_url)


        # client.ioLoop.start()

    def write_client(self, msg, other_port):
        print("self port: " + str(self.port) + " writes msg to other port: " + str(other_port))
        to_url = "ws://localhost:" + str(other_port)
        client = Client(5, self.port)
        client.write(msg, to_url)
        client.ioLoop.start()

    def test(self, msg):
        print("adsfa")

    # def open_client(self,other_port):
    #     url="ws://localhost:"+str(other_port)
    #     client = Client(url,5)
    #     client.connect()
    #     client.ioLoop.start()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    ]
        settings = dict(debug=True)
        self.ioloop = tornado.ioloop.IOLoop.instance()

        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    clients = set()

    def check_origin(self, origin):
        return True

    def open(self):
        print("A client connected.")
        MainHandler.clients.add(self)

    def on_close(self):
        print("A client disconnected")
        MainHandler.clients.remove(self)

    def send_to_client(self, msg):
        print("send message: {}".format(msg))
        self.write_message(msg)

    def on_message(self, message):
        print("server reads: " + message)
        for c in MainHandler.clients:
            if c != self:
                c.write_message(message)


class Client():

    def __init__(self, timeout, port):
        self.port = port;
        self.timeout = timeout
        self.ioLoop = IOLoop.instance()
        self.webSocket = None

    # @gen.coroutine
    # def connect(self, to_url):
    #     print("client trying to connect")

    #     self.webSocket = yield websocket_connect(to_url)

    @gen.coroutine
    def read(self, to_url):
        # print("client trying to read msg")
        # self.webSocket = yield websocket_connect(to_url)
        # msg = yield self.webSocket.read_message()
        # print("self port: " + str(self.port)+" reads: " +msg)

        self.webSocket = yield websocket_connect(to_url)
        while True:

            msg = yield self.webSocket.read_message()
            if msg is None:
                break
            else:
                print("self port: " + str(self.port) + " reads: " + msg)

    @gen.coroutine
    def write(self, msg, to_url):
        self.webSocket = yield websocket_connect(to_url)
        # print("client trying to write msg")
        # time.sleep(2)
        self.webSocket.write_message(msg)


if __name__ == "__main__":

    print("daffa")
    # node1 = Node(8080, [8090, 9000])
    # node2 = Node(8090, [8080, 9000])
    # node3 = Node(9000, [8090, 8080])

    manager = Manager()
    q = manager.Queue()
    node1 = Node(8080, [8090, 9000])
    node2 = Node(8090, [8080])
    node3 = Node(9000, [8080])

    pool = Pool(3)

    # pool.apply_async(node1.open_server)
    # pool.apply_async(node2.open_server)
    # pool.apply_async(node3.open_server)
    #
    # pool.apply_async(node3.read_client, (8080,))
    # pool.apply_async(node2.read_client, (8080,))
    # pool.apply_async(node1.read_client, (8090,))
    # pool.apply_async(node1.read_cliclent, (9000,))
    # # pool.apply_async(node3.read_client, (8080,))
    #
    # pool.apply_async(node3.write_client, ("this is 9000 connecting to 8080", 8080))

    pool.apply_async(node1.open_server)
    pool.apply_async(node2.open_server)
    pool.apply_async(node3.open_server)

    pool.apply(node3.read_client, (8080,))
    time.sleep(3)
    pool.apply(node2.read_client, (8080,))
    time.sleep(3)
    pool.apply(node1.read_client, (8090,))
    time.sleep(3)
    pool.apply(node1.read_client, (9000,))
    print()

    time.sleep(3)
    # pool.apply_async(node3.read_client, (8080,))

    pool.apply(node3.write_client, ("this is 9000 connecting to 8080", 8080))

    pool.close()

    while True:
        pool.join()

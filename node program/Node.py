
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options


class application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", main_handler),
                    ]
        settings = dict(debug=True)
        print("server starts")

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="progrom description")

    parser.add_argument('--port')
    parser.add_argument('--end')

    args = parser.parse_args()
    port = args.port
    end = args.end

    print(str(port) + " " + str(end))

    server = application()
    server.listen(port)

    if end == "1":
        tornado.ioloop.IOLoop.instance().start()

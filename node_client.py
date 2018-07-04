import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
from tornado.httpserver import HTTPServer

from tornado import gen
from tornado.websocket import websocket_connect

@gen.coroutine
def read(to_url):
    print("client trying to read msg")
    webSocket = yield websocket_connect(to_url)
    msg = yield webSocket.read_message()
            
@gen.coroutine
def write(to_url,msg,msgId):
    
    print("client trying to write msg")
    print(to_url)
    print(msg)
    webSocket = yield websocket_connect(to_url)
    webSocket.write_message(msg+";;;"+str(msgId))



import argparse

parser = argparse.ArgumentParser(description="program description")

parser.add_argument('--port')
parser.add_argument('--end')
parser.add_argument('--url')

args = parser.parse_args()
port = args.port
end = args.end
url = args.url

# url=["3000","8080"]
# for u in url:
#     to_url = "ws://localhost:" + u
#     print(to_url)

#     read(to_url)
    # if str(port)=="9000" and u == "8080":
    #     write(to_url,"test message",1)
    


to_url = "ws://localhost:" + args.url
print(to_url)
read(to_url)
if str(port)=="9000" and args.url == "8080":
    write(to_url,"test message",1)

tornado.ioloop.IOLoop.instance().start()

# read("ws://localhost:8080")
# tornado.ioloop.IOLoop.instance().start()











# from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen

import setting
import tree
import miner
import leader
import database

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", tree.NodeHandler),
                    (r"/buddy", tree.BuddyHandler),
                    (r"/available_branches", AvailableBranchesHandler),
                    (r"/disconnect", DisconnectHandler),
                    (r"/broadcast", BroadcastHandler),
                    (r"/dashboard", DashboardHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class AvailableBranchesHandler(tornado.web.RequestHandler):
    def get(self):
        branches = list(tree.available_branches)

        # parents = []
        # for node in NodeConnector.parent_nodes:
        #     parents.append([node.host, node.port])
        self.finish({"available_branches": branches,
                     "buddy":len(tree.available_buddies),
                     #"parents": parents,
                     "group_id": tree.current_groupid})

class DisconnectHandler(tornado.web.RequestHandler):
    def get(self):
        for connector in NodeConnector.parent_nodes:
            # connector.remove_node = False
            connector.conn.close()

        for connector in BuddyConnector.buddy_nodes:
            # connector.remove_node = False
            connector.conn.close()

        self.finish({})
        tornado.ioloop.IOLoop.instance().stop()

class BroadcastHandler(tornado.web.RequestHandler):
    def get(self):
        test_msg = ["TEST_MSG", setting.current_groupid, time.time(), uuid.uuid4().hex]

        forward(test_msg)
        self.finish({"test_msg": test_msg})

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        branches = list(setting.available_branches)
        branches.sort(key=lambda l:len(l[2]))

        parents = []
        self.write("<br>current_groupid: %s <br>" % setting.current_groupid)
        self.write("<br>available_branches:<br>")
        for branch in branches:
            self.write("%s %s %s <br>" %branch)

        self.write("<br>available_buddies: %s<br>" % len(setting.available_buddies))
        for buddy in setting.available_buddies:
            self.write("%s %s <br>" % buddy)

        self.write("<br>parent_nodes:<br>")
        for node in NodeConnector.parent_nodes:
            self.write("%s %s<br>" %(node.host, node.port))

        self.write("<br>available_children_buddies:<br>")
        for k,vs in setting.available_children_buddies.items():
            self.write("%s<br>" % k)
            for v1,v2 in vs:
                self.write("%s %s<br>" % (v1,v2))

        self.finish()

def main():
    tree.main()
    database.main()

    server = Application()
    server.listen(tree.current_port)
    tornado.ioloop.IOLoop.instance().add_callback(tree.connect)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

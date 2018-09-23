from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen

NODE_REDUNDANCY = 3

available_branches = set()
available_buddies = set()
available_children_buddies = dict()
current_branch = None
current_groupid = ""

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/node", NodeHandler),
                    (r"/buddy", BuddyHandler),
                    (r"/available_branches", AvailableBranchesHandler),
                    (r"/disconnect", DisconnectHandler),
                    (r"/broadcast", BroadcastHandler),
                    (r"/dashboard", DashboardHandler),
                    ]
        settings = {"debug":True}

        tornado.web.Application.__init__(self, handlers, **settings)


class AvailableBranchesHandler(tornado.web.RequestHandler):
    def get(self):
        global available_branches
        global available_buddies

        branches = list(available_branches)

        # parents = []
        # for node in NodeConnector.parent_nodes:
        #     parents.append([node.host, node.port])
        self.finish({"available_branches": branches,
                     "buddy":len(available_buddies),
                     #"parents": parents,
                     "group_id": current_groupid})

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
        global current_groupid
        test_msg = ["TEST_MSG", current_groupid, time.time()]

        for node in NodeHandler.child_nodes.values():
            node.write_message(json.dumps(test_msg))

        for connector in NodeConnector.parent_nodes:
            connector.conn.write_message(json.dumps(test_msg))

        self.finish({})

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        # global available_branches
        # global available_buddies

        branches = list(available_branches)
        branches.sort(key=lambda l:len(l[2]))

        parents = []
        self.write("<br>group_id: %s <br>" % current_groupid)
        self.write("<br>available_branches:<br>")
        for branch in branches:
            self.write("%s %s %s <br>" %branch)

        self.write("<br>buddy: %s<br>" % len(available_buddies))
        for buddy in available_buddies:
            self.write("%s %s <br>" % buddy)

        self.write("<br>parents:<br>")
        for node in NodeConnector.parent_nodes:
            self.write("%s %s<br>" %(node.host, node.port))

        self.write("<br>available_children_buddies:<br>")
        for k,vs in available_children_buddies.items():
            self.write("%s<br>" % k)
            for v1,v2 in vs:
                self.write("%s %s<br>" % (v1,v2))

        self.finish()

# connect point from child node
class NodeHandler(tornado.websocket.WebSocketHandler):
    child_nodes = dict()

    def check_origin(self, origin):
        return True

    def open(self):
        global available_branches
        global available_children_buddies

        self.branch = self.get_argument("branch")
        self.from_host = self.get_argument("host")
        self.from_port = self.get_argument("port")
        self.remove_node = True
        # print("branch", self.branch)
        if self.branch in NodeHandler.child_nodes:
            print(current_port, "force disconnect")
            self.remove_node = False
            self.close()
            return

        print(current_port, "child connected branch", self.branch)
        if self.branch not in NodeHandler.child_nodes:
            NodeHandler.child_nodes[self.branch] = self

        available_branches.remove(tuple([current_host, current_port, self.branch]))
        # print(current_port, "available branches open", available_branches)

        print(current_port, ["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]]])
        for node in NodeHandler.child_nodes.values():
            node.write_message(json.dumps(["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]]]))

        for connector in NodeConnector.parent_nodes:
            connector.conn.write_message(json.dumps(["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]]]))


        for node in BuddyHandler.buddy_nodes:
            if node != self:
                node.write_message(json.dumps(["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]]]))

        for connector in BuddyConnector.buddy_nodes:
            connector.conn.write_message(json.dumps(["DISCARDED_BRANCHES", [[current_host, current_port, self.branch]]]))


        buddies = list(available_children_buddies.get(self.branch, set()))
        self.write_message(json.dumps(["GROUP_ID", self.branch, buddies]))
        available_children_buddies.setdefault(self.branch, set()).add((self.from_host, self.from_port))

        # for node in BuddyHandler.buddy_nodes:
        #     if node != self:
        #         node.write_message(json.dumps(["AVAILABLE_BRANCHES", [[self.from_host, self.from_port, self.branch]]]))

        # for connector in BuddyConnector.buddy_nodes:
        #     connector.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[self.from_host, self.from_port, self.branch]]]))

    def on_close(self):
        global available_branches
        print(current_port, "child disconnected from parent")
        if self.branch in NodeHandler.child_nodes and self.remove_node:
            del NodeHandler.child_nodes[self.branch]
        self.remove_node = True

        available_branches.add(tuple([current_host, current_port, self.branch]))

        for node in NodeHandler.child_nodes.values():
            if node != self:
                node.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        for connector in NodeConnector.parent_nodes:
            connector.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))


        for node in BuddyHandler.buddy_nodes:
            if node != self:
                node.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        for connector in BuddyConnector.buddy_nodes:
            connector.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        # print(current_port, tuple([self.from_host, self.from_port, self.branch+"0"]))
        # print(current_port, tuple([self.from_host, self.from_port, self.branch+"1"]))

        available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"0"]))
        available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"1"]))

        for node in NodeHandler.child_nodes.values():
            if node != self:
                node.write_message(json.dumps(["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]]]))

        for connector in NodeConnector.parent_nodes:
            connector.conn.write_message(json.dumps(["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]]]))

        # for node in BuddyHandler.buddy_nodes:
        #     if node != self:
        #         node.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        # for connector in BuddyConnector.buddy_nodes:
        #     connector.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        # print(current_port, "available branches on_close", available_branches)


    @tornado.gen.coroutine
    def on_message(self, msg):
        global available_branches
        print(current_port, "on message from child", msg)
        seq = json.loads(msg)
        if seq[0] == "DISCARDED_BRANCHES":
            # print(seq[1])
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(branch_host, branch_port, branch)
                available_branches.remove(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.child_nodes.values():
                if node != self:
                    node.write_message(msg)

            for connector in NodeConnector.parent_nodes:
                connector.conn.write_message(msg)

            for node in BuddyHandler.buddy_nodes:
                if node != self:
                    node.write_message(msg)

            for connector in BuddyConnector.buddy_nodes:
                connector.conn.write_message(msg)

            # print(current_port, "available branches on_message", available_branches)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(branch_host, branch_port, branch)
                available_branches.add(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.child_nodes.values():
                if node != self:
                    node.write_message(msg)

            for connector in NodeConnector.parent_nodes:
                connector.conn.write_message(msg)

            for node in BuddyHandler.buddy_nodes:
                if node != self:
                    node.write_message(msg)

            for connector in BuddyConnector.buddy_nodes:
                connector.conn.write_message(msg)

            # print(current_port, "available branches on_message", available_branches)

        else:
            for node in NodeHandler.child_nodes.values():
                if node != self:
                    node.write_message(msg)

            for connector in NodeConnector.parent_nodes:
                connector.conn.write_message(msg)


# connector to parent node
class NodeConnector(object):
    """Websocket Client"""
    parent_nodes = set()

    def __init__(self, to_host, to_port, branch):
        self.host = to_host
        self.port = to_port
        self.branch = branch
        self.ws_uri = "ws://%s:%s/node?branch=%s&host=%s&port=%s" % (self.host, self.port, self.branch, current_host, current_port)
        self.conn = None
        self.connect()

    def connect(self):
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 10.0)

    def on_connect(self, future):
        global available_branches
        global parent_nodes
        print(current_port, "node connect")

        # try:
        self.conn = future.result()
        if self not in NodeConnector.parent_nodes:
            NodeConnector.parent_nodes.add(self)
        # except:
        #     print(current_port, "reconnect1 ...")
        #     tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)

        available_branches.add(tuple([current_host, current_port, self.branch+"0"]))
        available_branches.add(tuple([current_host, current_port, self.branch+"1"]))

        # for i in NodeHandler.child_nodes.values():
        #     i.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]]]))
        self.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]]]))


    def on_message(self, msg):
        global available_branches
        global available_buddies
        global current_branch
        global current_groupid
        if msg is None:
            # print("reconnect2 ...")
            available_branches.remove(current_branch)
            # available_branches = set([tuple(i) for i in branches])
            branches = list(available_branches)
            current_branch = tuple(branches[0])
            branch_host, branch_port, branch = current_branch
            self.ws_uri = "ws://%s:%s/node?branch=%s&from=%s" % (branch_host, branch_port, branch, branch_port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        print(current_port, "on message from parent", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(current_port, branch_host, branch_port, branch)
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.child_nodes.values():
                node.write_message(msg)

            # print(current_port, "available branches", available_branches)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(current_port, branch_host, branch_port, branch)
                available_branches.add(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.child_nodes.values():
                node.write_message(msg)

            # print(current_port, "available branches", available_branches)

        elif seq[0] == "GROUP_ID":
            # print(current_port, seq[1])
            current_groupid = seq[1]
            available_buddies = available_buddies.union(set([tuple(i) for i in seq[2]]))
            buddies_left = available_buddies - set([tuple([current_host, current_port])])
            buddies_left = buddies_left - set([(i.host, i.port) for i in BuddyConnector.buddy_nodes])
            buddies_left = buddies_left - set([(i.from_host, i.from_port) for i in BuddyHandler.buddy_nodes])
            for h, p in buddies_left:
                # print(current_port, "buddy to connect", h, p)
                BuddyConnector(h, p)

        else:
            for node in NodeHandler.child_nodes.values():
                node.write_message(msg)



# connect point from buddy node
class BuddyHandler(tornado.websocket.WebSocketHandler):
    buddy_nodes = set()

    def check_origin(self, origin):
        return True

    def open(self):
        global available_branches
        global available_buddies

        self.from_host = self.get_argument("host")
        self.from_port = self.get_argument("port")
        self.remove_node = True
        if False: #temp disable force disconnect
            print(current_port, "buddy force disconnect")
            self.remove_node = False
            self.close()
            return

        print(current_port, "buddy connected")
        if self not in BuddyHandler.buddy_nodes:
            BuddyHandler.buddy_nodes.add(self)

        available_buddies.add(tuple([self.from_host, self.from_port]))
        self.write_message(json.dumps(["GROUP_ID_FOR_BUDDY", current_groupid, list(available_buddies)]))

        # maybe it's wrong, we should tell buddy all the available branches existing
        self.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, current_groupid+"0"], [current_host, current_port, current_groupid+"1"]]]))


    def on_close(self):
        global available_branches
        print(current_port, "buddy disconnected")
        if self in BuddyHandler.buddy_nodes and self.remove_node:
            BuddyHandler.buddy_nodes.remove(self)
        self.remove_node = True

        # available_branches.add(tuple([current_host, current_port, self.branch]))

        # for node in BuddyHandler.buddy_nodes:
        #     if node != self:
        #         node.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        # for connector in BuddyConnector.buddy_nodes:
        #     connector.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch]]]))

        # print(current_port, tuple([self.from_host, self.from_port, self.branch+"0"]))
        # print(current_port, tuple([self.from_host, self.from_port, self.branch+"1"]))

        # available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"0"]))
        # available_branches.remove(tuple([self.from_host, self.from_port, self.branch+"1"]))

        # for node in BuddyHandler.buddy_nodes:
        #     if node != self:
        #         node.write_message(json.dumps(["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]]]))

        # for connector in BuddyConnector.buddy_nodes:
        #     connector.conn.write_message(json.dumps(["DISCARDED_BRANCHES", [[self.from_host, self.from_port, self.branch+"0"], [self.from_host, self.from_port, self.branch+"1"]]]))

        # print(current_port, "available branches on_close", available_branches)


    @tornado.gen.coroutine
    def on_message(self, msg):
        global available_branches
        global available_children_buddies
        seq = json.loads(msg)
        print(current_port, "on message from buddy connector", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            # print(seq[1])
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(branch_host, branch_port, branch)
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

            for node in BuddyHandler.buddy_nodes:
                if node != self:
                    node.write_message(msg)

            for connector in BuddyConnector.buddy_nodes:
                connector.conn.write_message(msg)

            # print(current_port, "available branches buddy on message", available_branches)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(branch_host, branch_port, branch)
                available_branches.add(tuple([branch_host, branch_port, branch]))
                available_children_buddies.setdefault(branch[:-1], set()).add((branch_host, branch_port))

            for node in BuddyHandler.buddy_nodes:
                if node != self:
                    node.write_message(msg)

            for connector in BuddyConnector.buddy_nodes:
                connector.conn.write_message(msg)

            # print(current_port, "available branches buddy on message", available_branches)

        else:
            for node in BuddyHandler.buddy_nodes:
                if node != self:
                    node.write_message(msg)

            for connector in BuddyConnector.buddy_nodes:
                connector.conn.write_message(msg)


# connector to buddy node
class BuddyConnector(object):
    """Websocket Client"""
    buddy_nodes = set()

    def __init__(self, to_host, to_port):
        self.host = to_host
        self.port = to_port
        self.ws_uri = "ws://%s:%s/buddy?host=%s&port=%s" % (self.host, self.port, current_host, current_port)
        self.branch = None
        self.conn = None
        self.connect()

    def connect(self):
        # print(current_port, self.ws_uri)
        tornado.websocket.websocket_connect(self.ws_uri,
                                callback = self.on_connect,
                                on_message_callback = self.on_message,
                                connect_timeout = 1000.0)

    def on_connect(self, future):
        global available_branches
        global parent_nodes
        print(current_port, "buddy connect")

        try:
            self.conn = future.result()
            # print(current_port, self.conn)
            if self not in BuddyConnector.buddy_nodes:
                BuddyConnector.buddy_nodes.add(self)
        except:
            print(current_port, "reconnect buddy ...")
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)

        # available_branches.add(tuple([current_host, current_port, self.branch+"0"]))
        # available_branches.add(tuple([current_host, current_port, self.branch+"1"]))

        # for i in NodeHandler.child_nodes.values():
        #     i.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]]]))
        if self.branch is not None:
            self.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]]]))


    def on_message(self, msg):
        global available_branches
        global available_buddies
        global available_children_buddies
        global current_branch
        global current_groupid
        if msg is None:
            # print("reconnect2 ...")
            available_branches.remove(current_branch)
            # available_branches = set([tuple(i) for i in branches])
            branches = list(available_branches)
            current_branch = tuple(branches[0])
            branch_host, branch_port, branch = current_branch
            self.ws_uri = "ws://%s:%s/node?branch=%s&from=%s" % (branch_host, branch_port, branch, branch_port)
            tornado.ioloop.IOLoop.instance().call_later(1.0, self.connect)
            return

        seq = json.loads(msg)
        print(current_port, "on message from buddy", seq)
        if seq[0] == "DISCARDED_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(current_port, branch_host, branch_port, branch)
                if tuple([branch_host, branch_port, branch]) in available_branches:
                    available_branches.remove(tuple([branch_host, branch_port, branch]))

            for node in NodeHandler.child_nodes.values():
                node.write_message(msg)

            # print(current_port, "available branches buddy", available_branches)

        elif seq[0] == "AVAILABLE_BRANCHES":
            for i in seq[1]:
                branch_host, branch_port, branch = i
                # print(current_port, branch_host, branch_port, branch)
                available_branches.add(tuple([branch_host, branch_port, branch]))
                available_children_buddies.setdefault(branch[:-1], set()).add((branch_host, branch_port))

            for node in NodeHandler.child_nodes.values():
                node.write_message(msg)

            # print(current_port, "available branches buddy", available_branches)

        elif seq[0] == "GROUP_ID_FOR_BUDDY":
            current_groupid = self.branch = seq[1]
            available_branches.add(tuple([current_host, current_port, current_groupid+"0"]))
            available_branches.add(tuple([current_host, current_port, current_groupid+"1"]))

            available_buddies = available_buddies.union(set([tuple(i) for i in seq[2]]))
            buddies_left = available_buddies - set([tuple([current_host, current_port])])
            buddies_left = buddies_left - set([(i.host, i.port) for i in BuddyConnector.buddy_nodes])
            buddies_left = buddies_left - set([(i.from_host, i.from_port) for i in BuddyHandler.buddy_nodes])
            for h, p in buddies_left:
                # print(current_port, "buddy to connect", h, p)
                BuddyConnector(h, p)
            # print(current_port, "available buddies", available_buddies)

            # print(current_port, seq[1], self.conn)
            if self.conn is not None:
                self.conn.write_message(json.dumps(["AVAILABLE_BRANCHES", [[current_host, current_port, self.branch+"0"], [current_host, current_port, self.branch+"1"]]]))

            # print(current_port, "available branches buddy", available_branches)

        else:
            for node in NodeHandler.child_nodes.values():
                node.write_message(msg)



# connector to control center
control_node = None
def on_connect(future):
    global control_node
    # print("on connect")

    try:
        control_node = future.result()
        control_node.write_message(json.dumps(["ADDRESS", current_host, current_port]))
    except:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)

@tornado.gen.coroutine
def on_message(msg):
    print(current_port, "node on message", msg)
    global control_node
    global available_branches
    global available_buddies
    global current_branch
    global current_groupid
    if msg is None:
        tornado.ioloop.IOLoop.instance().call_later(1.0, connect)
        return

    seq = json.loads(msg)
    if seq[0] == "BOOTSTRAP_ADDRESS":
        # print("BOOTSTRAP_ADDRESS", seq)
        if not seq[1]:
            # root node
            available_branches.add(tuple([current_host, current_port, "0"]))
            available_branches.add(tuple([current_host, current_port, "1"]))
            current_groupid = ""

            # print(current_port, "available branches", available_branches)
        elif len(seq[1]) < NODE_REDUNDANCY:
            print(current_port, "connect to root as buddy", seq[1])
            BuddyConnector(*seq[1][0])
        else:
            print(current_port, "fetch", seq[1][0])
            http_client = tornado.httpclient.AsyncHTTPClient()
            try:
                response = yield http_client.fetch("http://%s:%s/available_branches" % tuple(seq[1][0]))
            except Exception as e:
                print("Error: %s" % e)
            result = json.loads(response.body)
            branches = result["available_branches"]
            branches.sort(key=lambda l:len(l[2]))
            # buddy = result["buddy"]
            print(current_port, "fetch result", [tuple(i) for i in branches])

            available_branches = set([tuple(i) for i in branches])
            current_branch = tuple(branches[0])
            NodeConnector(*branches[0])

def connect():
    print("\n\n")
    print(current_port, "connect control", control_port)
    tornado.websocket.websocket_connect("ws://localhost:%s/control" % control_port, callback=on_connect, on_message_callback=on_message)

def main():
    global current_host
    global current_port
    global control_port
    global available_buddies

    parser = argparse.ArgumentParser(description="node description")
    parser.add_argument('--port')
    parser.add_argument('--control_port')

    args = parser.parse_args()
    current_host = "localhost"
    current_port = args.port
    control_port = args.control_port
    available_buddies.add(tuple([current_host, current_port]))

    server = Application()
    server.listen(current_port)
    tornado.ioloop.IOLoop.instance().add_callback(connect)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

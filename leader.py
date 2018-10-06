from __future__ import print_function

import time
import socket
import subprocess
import argparse
import json
import uuid

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpclient
import tornado.gen

import node

def main():
    print(node.Application.current_port, node.NODE_REDUNDANCY)

if __name__ == '__main__':
    # main()
    print("run python node.py pls")

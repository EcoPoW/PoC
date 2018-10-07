import torndb

NODE_REDUNDANCY = 3

db = torndb.Connection("127.0.0.1", "nodes", user="root", password="root")


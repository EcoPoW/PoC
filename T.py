#
# usage: python T.py|dot -Tpng > T.png

import random
import uuid
import pprint

nodes = [uuid.uuid4().hex for i in range(100)]
# print(nodes)

tree = {}
for node in nodes:
    depth = 1
    parent = tree
    n = tree.get(node[:depth])
    while True:
        n = parent.get(node[:depth])
        if n:
            depth += 1
            parent = n
        else:
            parent[node[:depth]] = {"_id":node}#, "children":{}, "parent":parent
            break

# pprint.pprint(tree)

print("digraph G {")
def list_tree(parent):
    for k in [k for k in parent.keys() if not k.startswith("_")]:
        if len(k) == 1:
            print('    "%s"->"R";'%(k))
        else:
            print('    "%s"->"%s";'%(k,k[:-1]))
        child = parent.get(k)
        if child:
            list_tree(child)

list_tree(tree)

print("}")

#
# usage: python G.py|dot -Tpng > G.png

import random

nodes = list(range(1,100))

print("digraph G {")
for node in nodes:
    to = random.choice(list(set(nodes) - set([node])))
    print("%s -> %s;" %(node, to))

print("}")

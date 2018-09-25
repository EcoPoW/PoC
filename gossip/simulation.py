from __future__ import print_function

import random
import copy


SIZE = 10000
# CONTACT = 100

got_msg = set()
user_friends = dict()
all_users = range(SIZE)

for f in range(SIZE):
    random.shuffle(all_users)
    friends = copy.copy(all_users)
    # friends = all_users[:CONTACT]
    # friends = list(set(friends) - set([f]))[:CONTACT]
    user_friends[f] = friends
    if not f % 100:
        print("progress:", f*100/SIZE)

got_msg.add(0)
gossip_round = 1
finish = False
while not finish:
    new_got_msg = set()
    for i in got_msg:
        friends = user_friends[i]
        if friends:
            t = friends.pop(0)
            user_friends[i] = friends
            if t not in got_msg:
                new_got_msg.add(t)

    print("round", gossip_round, "infect", len(got_msg))
    if len(got_msg) == SIZE:
        finish = True

    got_msg = got_msg.union(new_got_msg)
    gossip_round += 1

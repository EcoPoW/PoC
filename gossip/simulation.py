from __future__ import print_function

import random


SIZE = 50000
CONTACT = 40

got_msg = set()
user_friends = dict()
all_users = range(SIZE)

for f in range(SIZE):
    random.shuffle(all_users)
    friends = all_users[:CONTACT]
    # friends = list(set(friends) - set([f]))[:CONTACT]
    user_friends[f] = friends
    if not f % 100:
        print("progress:", f*100/SIZE)

for i in range(CONTACT):
    for f in user_friends:
        friends = user_friends[f]
        t = friends.pop(0)
        user_friends[f] = friends
        if t not in got_msg:
            got_msg.add(t)

    print("round", i, "infect", len(got_msg))

# nodes

start control

    python3 control.py [--control_port=8000]

start node

    python3 node.py --port=8001 --control_port=8000

or

    curl 127.0.0.1:8000/new_node

python 3.4+ (or 2.7.9+)

ubuntu 14.04

    sudo apt install mysql-server python3-pip openssl libssl-dev libffi-dev
    sudo pip3 install -U tornado pymysql setuptools

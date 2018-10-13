# nodes

start control

    python3 control.py

start node

    curl http://127.0.0.1:8000/new_node (or in browser)

or manually

    python3 node.py --port=8001 --control_port=8000

python 3.4+ (or 2.7.9+)

Ubuntu 14.04 LTS

    sudo apt install mysql-server python3-pip openssl libssl-dev libffi-dev
    sudo pip3 install -U tornado pymysql setuptools

Mac

    brew install mysql python3
    pip3 install -U tornado pymysql setuptools

Anaconda/miniconda

    conda install -U tornado pymysql

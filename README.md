# MTFS PoC

Start dashboard in cmd line:

    python3 dashboard.py

Visualize in browser:

    http://127.0.0.1:8000/static/index.html

Start node:

    curl http://127.0.0.1:8000/new_node (or in browser)

or manually in cmd line:

    python3 node.py --port=8001 --control_port=8000

Python 3.5+ required.

Ubuntu 14.04 LTS

    sudo apt install mysql-server python3 python3-pip openssl libssl-dev libffi-dev
    sudo pip3 install -U setuptools pip
    sudo pip3 install -r requirements.txt

macOS

    brew install mysql python3

or install Anaconda/miniconda python3 on Windows or macOS

Then

    pip3 install -U setuptools pip
    pip3 install -r requirements.txt

Database Requirement: MySQL 5.0+.

    CREATE DATABASE nodes;

## Related Paper

    https://arxiv.org/abs/1902.09100

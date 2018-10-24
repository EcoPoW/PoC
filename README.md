# nodes

start dashboard

    python3 dashboard.py

start node

    curl http://127.0.0.1:8000/new_node (or in browser)

or manually

    python3 node.py --port=8001 --control_port=8000

python 3.4+ (or 2.7.9+)

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

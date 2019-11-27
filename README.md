# MTFS: Message Transaction & File System

 * 高容量高性能区块链
 * 实时区块链，可用于支付，聊天等低延迟应用
 * 基于代理重加密的安全和隐私保护
 * 站在巨人的肩膀上，使用久经考验的 Python，MySQL 技术栈
 * 不使用传统P2P网络
 * 无Token区块链
 * 不使用零知识证明

本项目设计目标是生产环境使用，同时也为学术研究服务。目前暂未考虑商业化，也没有发币计划。
本项目目前并没有使用生产级别的高性能语言如rust，c++, java, go等进行性能优化。我们希望在理论上找到空间优化区块链网络整体，而不是压榨单机性能或增加硬件。


Start dashboard in terminal:

    python3 dashboard.py

Visualize in browser:

    http://127.0.0.1:8000/static/index.html

Start node:

    curl http://127.0.0.1:8000/new_node (or in browser)

or manually in terminal:

    python3 node.py --host=127.0.0.1 --port=8001 --control_host=127.0.0.1 --control_port=8000

Python 3.6+ required.

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

## 相关论文

    https://arxiv.org/abs/1902.09100
    
    https://arxiv.org/abs/1810.12795
    
    https://arxiv.org/abs/1808.10810

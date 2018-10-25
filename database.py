import torndb

import tree

connection = torndb.Connection("127.0.0.1", "nodes", user="root", password="root")

create_chain = """CREATE TABLE `chain%s` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `hash` varchar(64) NOT NULL DEFAULT '',
    `prev_hash` varchar(64) NOT NULL DEFAULT '',
    `nonce` int(11) unsigned NOT NULL,
    `difficulty` smallint(5) unsigned NOT NULL,
    `identity` varchar(66) NOT NULL DEFAULT '',
    `timestamp` int(11) unsigned NOT NULL,
    `data` mediumtext NOT NULL,
    PRIMARY KEY (`id`),
    KEY `identity` (`identity`),
    UNIQUE KEY `hash` (`hash`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
"""

create_graph = """CREATE TABLE `graph%s` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `transaction_id` int(11) unsigned DEFAULT NULL,
    `timestamp` int(11) unsigned DEFAULT NULL,
    `hash` varchar(128) NOT NULL DEFAULT '',
    `from_block` varchar(128) NOT NULL DEFAULT '',
    `to_block` varchar(128) NOT NULL DEFAULT '',
    `nonce` int(10) unsigned NOT NULL,
    `sender` varchar(128) NOT NULL,
    `receiver` varchar(128) NOT NULL,
    `data` text NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `hash` (`hash`),
    UNIQUE KEY `block_nonce` (`from_block`,`to_block`,`nonce`),
    KEY `from_block` (`from_block`,`sender`,`nonce`),
    KEY `to_block` (`to_block`,`receiver`,`nonce`)
) ENGINE=InnoDB AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8;
"""

# create_users = """CREATE TABLE `%susers` (
#     `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
#     `user_id` char(70) NOT NULL DEFAULT '',
#     `hash` char(32) NOT NULL DEFAULT '',
#     `node_id` varchar(100) NOT NULL DEFAULT '',
#     `object_size` int(10) unsigned NOT NULL,
#     `folder_size` int(10) unsigned NOT NULL,
#     `timestamp` int(10) unsigned NOT NULL,
#     `replication_id` tinyint(3) unsigned NOT NULL,
#     PRIMARY KEY (`id`),
#     KEY `user_id` (`user_id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
# """

# create_roots = """CREATE TABLE `%sroots` (
#     `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
#     `hash` char(32) NOT NULL DEFAULT '',
#     `size` int(10) unsigned NOT NULL,
#     `timestamp` int(10) unsigned NOT NULL,
#     `tree` text NOT NULL,
#     PRIMARY KEY (`id`),
#     KEY `hash` (`hash`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
# """


def main():
    # if not connection.get("SELECT table_name FROM information_schema.tables WHERE table_schema = 'nodes' AND table_name = %s", tree.current_port+"chain"):
    connection.execute("DROP TABLE IF EXISTS %schain" % tree.current_port)
    connection.execute("DROP TABLE IF EXISTS chain%s" % tree.current_port)
    connection.execute(create_chain % tree.current_port)
    # connection.execute("TRUNCATE %schain" % tree.current_port)

    connection.execute("DROP TABLE IF EXISTS %sgraph" % tree.current_port)
    connection.execute("DROP TABLE IF EXISTS graph%s" % tree.current_port)
    connection.execute(create_graph % tree.current_port)

    connection.execute("DROP TABLE IF EXISTS %susers" % tree.current_port)
    # connection.execute(create_users % tree.current_port)

    connection.execute("DROP TABLE IF EXISTS %sroots" % tree.current_port)
    # connection.execute(create_roots % tree.current_port)

import torndb

import tree

connection = torndb.Connection("127.0.0.1", "nodes", user="root", password="root")

create_chain = """CREATE TABLE `%schain` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `hash` varchar(64) NOT NULL DEFAULT '',
  `prev_hash` varchar(64) NOT NULL DEFAULT '',
  `nonce` int(11) unsigned NOT NULL,
  `wallet_address` varchar(32) NOT NULL DEFAULT '',
  `data` mediumtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
"""

def main():
    if not connection.get("SELECT table_name FROM information_schema.tables WHERE table_schema = 'nodes' AND table_name = %s", tree.current_port+"chain"):
        connection.execute(create_chain % tree.current_port)
    connection.execute("TRUNCATE "+tree.current_port+"chain")

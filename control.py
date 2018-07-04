import subprocess
import time
# q1 = subprocess.call(["python","node.py","--port","9090","--end","0"])
# q2 = subprocess.call(["python","node.py","--port","9010","--end","0"])
# q3 = subprocess.call(["python","node.py","--port","8080","--end","1"])
import tornado
import tornado.ioloop
from multiprocessing import Process,Pool,Queue,Manager


d={
    8000:[8010,8090],
    8010:[8000],
    8090:[8000],
    "last_port":8090,


}

#end的赋值还需要改进，原则上是执行最后一个port的最后一个客户端， end才赋值为1，现在先假设最后一个port只有一个peer

# for port in d.keys():
#     if port != "last":

#         # end = "0"
#         # if port == d["last"]:
#         #     end = "1"

#         subprocess.call(["python3", "test1.py", "--port", str(port), "--end", "0", "--url", "0"])

def open_server(port,peer):
    subprocess.call(["python3", "node_server.py", "--port", str(port), "--peer",peer, "--url", "0"])

def read(port1,port2):
    subprocess.call(["python3", "node_client.py", "--port", str(port1), "--end", "0", "--url", str(port2)])

# subprocess.call(["python3", "node_server.py", "--port", str(8080), "--end", "0", "--url", "0"])
# subprocess.call(["python3", "node_server.py", "--port", str(3000), "--end", "0", "--url", "0"])
# subprocess.call(["python3", "node_server.py", "--port", str(9000), "--end", "0", "--url", "0"])

# time.sleep(3)
# subprocess.call(["python3", "client.py", "--port", str(9000), "--end", "1", "--url", "3000"])
# subprocess.call(["python3", "client.py", "--port", str(9000), "--end", "1", "--url", "8080"])
pool = Pool(8)
pool.apply_async(open_server,(8080,"4000,3000",))
pool.apply_async(open_server,(3000,"",))
pool.apply_async(open_server,(9000,"",))
pool.apply_async(open_server,(4000,"",))
time.sleep(3)
pool.apply_async(read,(9000,8080,))
pool.apply_async(read,(4000,8080,))

pool.close()

pool.join()


# for port in d.keys():
#     if port != "last":
#         end = "0"

#         if port == d["last"]:
#             end = "1"
#         peer_ports = d[port]
#         for peer in peer_ports:

#             subprocess.call(["python3", "test1.py", "--port", str(port), "--end", end, "--url", str(peer)])

import subprocess
import time
import tornado
import tornado.ioloop
from multiprocessing import Process,Pool,Queue,Manager
import socket
import json
import pickle

def open_server(port):
    # subprocess.call(["python3", "node_server.py", "--port", str(port), "--peer",peer, "--url", "0"])
    subprocess.call(["python3", "node.py", "--port1", str(port), "--port2","", "--operation", "0","--message",""])
def read(port1,port2,message):
    # subprocess.call(["python3", "node_client.py", "--port1", str(port1), "--port2",str(port2),"--message",message])
    subprocess.call(["python3", "node.py", "--port1", str(port1), "--port2",str(port2), "--operation", "1","--message",message])

def broadcast(port1,message):
	subprocess.call(["python3", "node.py", "--port1", str(port1), "--port2","", "--operation", "2","--message",message])

def ping(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost',int(port)))
    print("result:"+str(result))

def add_node():
	pool.apply_async(open_server,(4001+len(tree),))
	time.sleep(1)
	for i in range (4002,4001+len(tree)):
		print(str(i)+str(tree[str(i)]))
		if len(tree[str(i)])<3:
			temp=tree[str(i)]
			temp.append(str(4001+len(tree)))
			tree[str(i)]=temp
			tree[str(4001+len(tree))]=[str(i)]
			break
	for ii in range (4001,4001+len(tree)):
		with open(str(ii), 'wb') as f:
			pickle.dump(tree,f)


tree={"4001":["4002","4003"],
	"4002":["4001","4004","4005"],
	"4003":["4001","4006","4007"],
	"4004":["4002"],
	"4005":["4002"],
	"4006":["4003"],
	"4007":["4003"]}

print("'"+json.dumps(tree)+"'")


for i in range (4001,4008):
	with open(str(i), 'wb') as f:
		pickle.dump(tree,f)


pool = Pool(20)
pool.apply_async(open_server,(4001,))
pool.apply_async(open_server,(4002,))
pool.apply_async(open_server,(4003,))
pool.apply_async(open_server,(4004,))
pool.apply_async(open_server,(4005,))
pool.apply_async(open_server,(4006,))
pool.apply_async(open_server,(4007,))
# pool.apply_async(open_server,(4008,))
# pool.apply_async(open_server,(4009,))
# pool.apply_async(open_server,(4010,))
# pool.apply_async(open_server,(4011,))

time.sleep(3)

list1 = ["Google"]
list1.append("Baidu")
print(["aa"].append("bb"))


while True:
    command=str(input("Input command: "))
    
    if command[0] == "0":
        port=command.split(";")[1]
        ping(port)
    if command[0] == "1":
        port1=command.split(";")[1]
        port2=command.split(";")[2]
        message=command.split(";")[3]
        pool.apply_async(read,(port1,port2,message))
    if command[0] == "2":
    	port1=command.split(";")[1]
    	message=command.split(";")[2]
    	with open(port1+'.txt','a') as f:
    		f.write(message+"\n")
    	time.sleep(1)
    if command[0] == "3":
    	pool.apply_async(broadcast,(4002,"First Message",)) 
    	time.sleep(1)
    if command[0] == "4":
    	add_node()
    	add_node()
    	add_node()
    	add_node()
    	time.sleep(1)

        # port1=command.split(";")[1]
        # with open(port1+'.txt', 'a') as f:
        # f.write('Hello, world!')
        # time.sleep(1)

print(qweqweqe)

# pool.apply_async(read,(9000,8080,))
# pool.apply_async(read,(4000,8080,))

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

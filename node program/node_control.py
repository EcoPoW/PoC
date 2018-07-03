import subprocess
import time
# q1 = subprocess.call(["python","node.py","--port","9090","--end","0"])
# q2 = subprocess.call(["python","node.py","--port","9010","--end","0"])
# q3 = subprocess.call(["python","node.py","--port","8080","--end","1"])
import tornado

d={
    8000:[8010,8090],
    8010:[8000],
    8090:[8000],
    "last_port":8090,


}

#end的赋值还需要改进，原则上是执行最后一个port的最后一个客户端， end才赋值为1，现在先假设最后一个port只有一个peer

for port in d.keys():
    if port != "last":

        # end = "0"
        # if port == d["last"]:
        #     end = "1"

        subprocess.call(["python", "node.py", "--port", str(port), "--end", "0", "--url", "0"])

time.sleep(3)

for port in d.keys():
    if port != "last":
        end = "0"

        if port == d["last"]:
            end = "1"
        peer_ports = d[port]
        for peer in peer_ports:

            subprocess.call(["python", "node.py", "--port", str(port), "--end", end, "--url", str(peer)])

# for i in range(0,10,1):
#     port = 8000+i
#     end = "0"
#     if i ==9:
#         end = "1"
#
#     subprocess.call(["python", "node.py", "--port", str(port), "--end", end,"--url","0"])
#
#     subprocess.call(["python", "node.py", "--port", str(port), "--end", end,"--url","8000"])

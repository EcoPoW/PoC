import subprocess
# q1 = subprocess.call(["python","node.py","--port","9090","--end","0"])
# q2 = subprocess.call(["python","node.py","--port","9010","--end","0"])
# q3 = subprocess.call(["python","node.py","--port","8080","--end","1"])

for i in range(0,10,1):
    port = 8000+i
    end = "0"
    if i ==9:
        end = "1"
    subprocess.call(["python", "node.py", "--port", str(port), "--end", end])

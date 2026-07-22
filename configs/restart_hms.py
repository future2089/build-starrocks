import subprocess

# Kill Metastore on 181 host
r = subprocess.run("ssh root@192.168.0.181 docker exec hadoop-arm ps aux | grep '[m]etastore'",
    shell=True, capture_output=True, text=True, timeout=15)
print('HMS before:', r.stdout[:100])

# Kill by host PID
r = subprocess.run("ssh root@192.168.0.181 ss -tlnp", shell=True, capture_output=True, text=True, timeout=15)
for line in r.stdout.split('\n'):
    if '9083' in line:
        print('Port 9083:', line[:100])

# Kill the hadoop-arm container's metastore via host signal
# Find host PID
r = subprocess.run("ssh root@192.168.0.181 docker inspect hadoop-arm --format '{{.State.Pid}}'",
    shell=True, capture_output=True, text=True, timeout=15)
container_pid = r.stdout.strip()
print('Container PID:', container_pid)

# Find the HMS PID on host
r = subprocess.run(f"ssh root@192.168.0.181 ps aux | grep '[m]etastore' | awk '{{print $2}}'",
    shell=True, capture_output=True, text=True, timeout=15)
hms_pid = r.stdout.strip()
print('HMS host PID:', hms_pid)

if hms_pid:
    subprocess.run(f"ssh root@192.168.0.181 kill -9 {hms_pid}", shell=True, timeout=15)
    print('HMS KILLED')

# Restart HMS
r = subprocess.run("ssh root@192.168.0.181 docker exec -d -e HADOOP_HOME=/data/package/hadoop-3.3.6 -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/apache-hive-3.1.3-bin/bin/hive --service metastore -p 9083",
    shell=True, capture_output=True, text=True, timeout=15)
print('HMS restart:', r.stdout[:100], r.stderr[:200])

import time
time.sleep(3)

r = subprocess.run("ssh root@192.168.0.181 s s -tlnp | grep 9083",
    shell=True, capture_output=True, text=True, timeout=15)
print('Port 9083 after restart:', r.stdout[:100])

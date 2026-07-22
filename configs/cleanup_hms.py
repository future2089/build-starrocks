import subprocess, time

# Kill all metastore processes on host 181
r = subprocess.run("ssh root@192.168.0.181 \"ps aux | grep '[m]etastore' | awk '{print \\$2}' | xargs -r kill -9\"", 
    shell=True, capture_output=True, text=True, timeout=15)
print('Kill result:', r.returncode, r.stderr[:100])

# Remove Derby locks inside container
r = subprocess.run("ssh root@192.168.0.181 docker exec hadoop-arm rm -f /var/hive/metastore/db.lck /var/hive/metastore/dbex.lck",
    shell=True, capture_output=True, text=True, timeout=15)
print('Remove locks:', r.returncode, r.stderr[:100])

# Check no metastore running
time.sleep(2)
r = subprocess.run("ssh root@192.168.0.181 ss -tlnp | grep 9083",
    shell=True, capture_output=True, text=True, timeout=15)
print('Port 9083 before start:', r.stdout[:100])

# Start HMS
r = subprocess.run("ssh root@192.168.0.181 docker exec -d -e HADOOP_HOME=/data/package/hadoop-3.3.6 -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/apache-hive-3.1.3-bin/bin/hive --service metastore -p 9083",
    shell=True, capture_output=True, text=True, timeout=15)
print('Start result:', r.returncode, r.stderr[:100])

# Wait and verify
time.sleep(5)
r = subprocess.run("ssh root@192.168.0.181 ss -tlnp | grep 9083",
    shell=True, capture_output=True, text=True, timeout=15)
print('Port 9083 after start:', r.stdout[:100])

r = subprocess.run("ssh root@192.168.0.181 docker exec hadoop-arm tail -3 /tmp/root/hive.log",
    shell=True, capture_output=True, text=True, timeout=15)
print('HMS log:', r.stdout[:300])

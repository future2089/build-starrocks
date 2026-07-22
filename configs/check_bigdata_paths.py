import subprocess

# Check correct paths for Hadoop/Hive
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'ls -la /data/bigdata/ 2>/dev/null; echo ===; ls -la /data/bigdata/hadoop-3.3.6/sbin/start-dfs.sh /data/bigdata/apache-hive-3.1.3-bin/bin/hive 2>/dev/null' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:1000])

# Check if HDFS needs formatting
r2 = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'ls -la /tmp/hadoop/name/current 2>/dev/null || echo \"No name dir\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print('\nHDFS name dir:')
print(r2.stdout.strip())

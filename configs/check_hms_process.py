import subprocess

# Check the running Hive metastore process and its ports
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'ps aux | grep HiveMetaStore | grep -v grep; echo ---; ss -tlnp | grep 9083; echo ---; ss -tlnp | grep -E \"9083|10000|8020|9866|50070\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:1000])

# Check the HMS log
r2 = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'cat /tmp/hive.log 2>/dev/null | tail -30 || cat /data/bigdata/apache-hive-3.1.3-bin/logs/hive.log 2>/dev/null | tail -30' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print('\nHMS log tail:')
print(r2.stdout.strip()[:1000])

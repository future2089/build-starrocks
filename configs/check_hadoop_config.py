import subprocess

# Check Hadoop/Hive config and any start scripts
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'docker exec hadoop-arm bash -c \"cat /etc/hadoop/conf/core-site.xml 2>/dev/null; echo ===; cat /etc/hadoop/conf/hdfs-site.xml 2>/dev/null; echo ===; cat /etc/hadoop/conf/hadoop-env.sh 2>/dev/null | head -10; echo ===; cat /data/package/apache-hive-3.1.3-bin/conf/hive-site.xml 2>/dev/null | head -60\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=20
)
print(r.stdout.strip()[:3000])
print('STDERR:', r.stderr.strip()[:300] if r.stderr else '')

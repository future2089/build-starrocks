import subprocess

# Check what's inside hadoop-arm container
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'docker exec hadoop-arm bash -c \"ls -la /opt/ /usr/local/ 2>/dev/null; ls -la /etc/hadoop/ /etc/hive/ 2>/dev/null; find / -name start-dfs.sh -o -name start-hiveserver2.sh -o -name hive-metastore -o -name hive 2>/dev/null | head -20\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=20
)
print(r.stdout.strip()[:2000])
print('STDERR:', r.stderr.strip()[:500] if r.stderr else '')

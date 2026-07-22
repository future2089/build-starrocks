import subprocess

# Get full process list on 181 host
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'ps aux | grep -E \"HiveMetaStore|HiveServer2|NameNode|DataNode\" | grep -v grep' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print('Host processes:')
print(r.stdout.strip()[:2000])

# Check all listening ports on 181
r2 = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'ss -tlnp' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print('\nAll listening ports:')
print(r2.stdout.strip()[:2000])

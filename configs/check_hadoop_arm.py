import subprocess

# Check inside hadoop-arm container
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'docker exec hadoop-arm ps aux | grep -E \"NameNode|DataNode|HiveMeta|RunJar|hive\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print('Processes inside hadoop-arm:')
print(r.stdout.strip()[:2000])

# Check port listening on 181 host
r2 = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'ss -tlnp | grep -E \"9083|8020|9866|9870|9000|9001\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print('\nListening ports:')
print(r2.stdout.strip())

import subprocess
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm tail -20 /tmp/hadoop-logs/metastore.log'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000] or "(empty)")
print(r.stderr.strip()[:300] if r.stderr else '')

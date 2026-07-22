import subprocess
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm bash -c "tail -5 /tmp/hadoop-logs/metastore.log; echo ---; ps aux | grep metastore | grep -v grep | head -3"'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:1500] or "(empty)")
print(r.stderr.strip()[:200] if r.stderr else '')

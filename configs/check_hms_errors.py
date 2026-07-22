import subprocess
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm grep -i "error\|exception\|fail\|locked" /tmp/hadoop-logs/metastore.log | head -20'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000] or "(no errors found)")
# Also check all log lines for key info
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm head -60 /tmp/hadoop-logs/metastore.log'],
    capture_output=True, text=True, timeout=15
)
print("\n=== Log head ===")
print(r2.stdout.strip()[:2000] or "(empty)")

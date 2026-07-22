import subprocess

# Check HMS status
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm sh -c "sleep 5; netstat -tlnp 2>/dev/null | grep 9083"'],
    capture_output=True, text=True, timeout=30
)
print("=== Port 9083 ===")
print(r.stdout.strip() or '(not listening)')
print(r.stderr.strip()[:300] if r.stderr else '')

# Check hadoop-arm log for errors
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm tail -20 /tmp/hadoop-logs/metastore.log'],
    capture_output=True, text=True, timeout=15
)
print("\n=== Metastore log (last 20 lines) ===")
print(r2.stdout.strip()[:1500] or '(empty)')
print(r2.stderr.strip()[:300] if r2.stderr else '')

import subprocess

# Check directory state and full derby error
script = r"""echo "=== /var/hive/metastore/ ==="
ls -la /var/hive/ 2>/dev/null
ls -la /var/hive/metastore/ 2>/dev/null || echo "(directory missing)"

echo "=== derby.log tail ==="
tail -20 /derby.log 2>/dev/null || echo "(no derby.log)"

echo "=== metastore.log tail ==="
tail -20 /tmp/hadoop-logs/metastore.log 2>/dev/null
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_derby_dir.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_derby_dir.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
print("STDERR:", r2.stderr.strip()[:300] if r2.stderr else '')

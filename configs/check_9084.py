import subprocess

script = r"""echo "=== Check port 9084 ==="
sleep 10
ss -tlnp 2>/dev/null | grep 9084 || netstat -tlnp 2>/dev/null | grep 9084 || echo "STILL NOT LISTENING"
echo "=== Full log ==="
tail -30 /tmp/hadoop-logs/metastore-9084.log 2>/dev/null || echo "(log not found)"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_9084.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_9084.sh'],
    capture_output=True, text=True, timeout=30
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

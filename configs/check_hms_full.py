import subprocess

script = r"""echo "=== Check if HMS process is alive ==="
ps aux | grep "[m]etastore.*apache-hive" | grep -v grep | awk '{print "PID="$2" ELAPSED=" $9}'
echo "=== Full log ==="
cat /tmp/hadoop-logs/metastore-9084.log 2>/dev/null
echo "=== Check derby.log ==="
cat /derby.log 2>/dev/null | head -30
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_hms_full.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_hms_full.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

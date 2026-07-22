import subprocess

script = r"""echo "=== Processes holding 9083 ==="
fuser 9083/tcp 2>/dev/null || true
netstat -tlnp 2>/dev/null | grep 9083 || true
echo "=== Current HMS processes ==="
ps aux | grep metastore | grep -v grep || echo "(none)"
echo "=== Find metastore_db ==="
find /tmp /root /var -name "metastore_db" -type d 2>/dev/null | head -5
echo "=== Find lock files ==="
find /tmp /root /var -name "db.lck" -o -name "*.lck" 2>/dev/null | head -10
echo "=== Current working dir ==="
pwd
ls -la
"""

# Write script to 211
subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/diag_hms.sh'],
    input=script, text=True, capture_output=True, timeout=10
)

# Execute on hadoop-arm via SSH to 181
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/diag_hms.sh'],
    capture_output=True, text=True, timeout=20
)
print(r.stdout.strip()[:2000] or "(empty)")
print("STDERR:", r.stderr.strip()[:300] if r.stderr else '')

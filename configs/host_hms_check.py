import subprocess

script = r"""echo "=== Host HMS check ==="
ps aux | grep "[m]etastore" | grep -v grep | head -2
echo "=== Port 9083 ==="
ss -tlnp 2>/dev/null | grep 9083 || netstat -tlnp 2>/dev/null | grep 9083 || echo "NO TOOL"
echo "=== Host HMS config ==="
cat /usr/hdp/current/hive-metastore/conf/hive-site.xml 2>/dev/null | grep -i "jdo\|derby\|connection\|thrift.*9083\|9083" | head -10
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/host_hms_check.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'bash < /tmp/host_hms_check.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

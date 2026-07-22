import subprocess

script = r"""echo "=== hive-site.xml JDBC config ==="
grep -i "jdo\|derby\|connection" /data/package/apache-hive-3.1.3-bin/conf/hive-site.xml 2>/dev/null || echo "(none)"

echo "=== Full derby.log ==="
cat /derby.log 2>/dev/null || echo "(none)"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_full_derby.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_full_derby.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:3000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

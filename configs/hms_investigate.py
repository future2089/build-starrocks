import subprocess

script = r"""echo "=== Host HMS config ==="
CONF=/usr/hdp/current/hive-metastore/conf/hive-site.xml
grep -iE "jdo|derby|connection|thrift.*9083|fs.default|namenode|metastore.uri|principal|keytab|kerberos|sasl" "$CONF" 2>/dev/null | head -20

echo "=== Container HMS PID ==="
ps aux | grep "[d]ata/package/apache-hive" | awk '{print "PID="$2" CMD="$0}' | head -2

echo "=== Which process has 9083? ==="
fuser 9083/tcp 2>/dev/null || ss -tlnp 2>/dev/null | grep 9083 || netstat -tlnp 2>/dev/null | grep 9083
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/hms_investigate.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'bash < /tmp/hms_investigate.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

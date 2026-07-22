import subprocess

script = r"""echo "=== HDFS NN status ==="
ps aux | grep -i "[N]ame[N]ode" | head -2
echo "=== Hadoop config ==="
ls /data/package/hadoop-3.3.6/etc/hadoop/ 2>/dev/null
echo "=== core-site.xml ==="
cat /data/package/hadoop-3.3.6/etc/hadoop/core-site.xml 2>/dev/null | head -20
echo "=== hdfs-site.xml ==="
cat /data/package/hadoop-3.3.6/etc/hadoop/hdfs-site.xml 2>/dev/null | head -30
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_hdfs.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_hdfs.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

import subprocess

script = r"""echo "=== Disk space ==="
df -h /var/hive/ /tmp/ 2>/dev/null
echo "=== Write test ==="
touch /var/hive/test_write 2>&1 && echo "WRITE OK" || echo "WRITE FAIL"
rm -f /var/hive/test_write
echo "=== Try /tmp instead ==="
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
sed 's|/var/hive/metastore|/tmp/metastore|' $HIVE_HOME/conf/hive-site.xml > /tmp/hive-site-tmp.xml
HIVE_CONF_DIR=/tmp $HIVE_HOME/bin/schematool -dbType derby -initSchema 2>&1 | tail -5
echo "=== /tmp/metastore ==="
ls -la /tmp/metastore/ 2>/dev/null | head -10
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/derby_test.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/derby_test.sh'],
    capture_output=True, text=True, timeout=30
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

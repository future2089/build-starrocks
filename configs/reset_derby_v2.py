import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

echo "1. Clean up completely"
rm -rf /var/hive/metastore
rm -f /derby.log

echo "2. Create fresh directory"
mkdir -p /var/hive/metastore

echo "3. Init schema from /var/hive"
cd /var/hive
$HIVE_HOME/bin/schematool -dbType derby -initSchema 2>&1 | tail -10

echo "4. Verify DB created"
ls -la /var/hive/metastore/

echo "5. Start HMS (from /var/hive)"
cd /var/hive
nohup $HIVE_HOME/bin/hive --service metastore -p 9083 > /tmp/hadoop-logs/metastore.log 2>&1 &
echo "HMS PID: $!"
sleep 10

echo "6. Verify port"
netstat -tlnp 2>/dev/null | grep 9083 || echo "(not listening)"

echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/reset_derby2.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/reset_derby2.sh'],
    capture_output=True, text=True, timeout=120
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:500] if r2.stderr else ''
if err: print("STDERR:", err)

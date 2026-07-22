import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

echo "1. Kill current HMS"
ps aux | grep metastore | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2

echo "2. Remove Derby database"
rm -rf /var/hive/metastore/*

echo "3. Re-initialize schema"
$HIVE_HOME/bin/schematool -dbType derby -initSchema 2>&1 | tail -5

echo "4. Start HMS"
nohup $HIVE_HOME/bin/hive --service metastore -p 9083 > /tmp/hadoop-logs/metastore.log 2>&1 &
echo "HMS PID: $!"
sleep 8

echo "5. Verify port"
netstat -tlnp 2>/dev/null | grep 9083 || echo "(not listening yet)"
echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/reset_hms_derby.sh'],
    input=script, text=True, capture_output=True, timeout=10
)

r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/reset_hms_derby.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()
if err:
    print("STDERR:", err[:300])

import subprocess

hms_script = """export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

# Check HDFS status
echo "=== HDFS ==="
jps 2>/dev/null | grep -E 'NameNode|DataNode'

# Check if NameNode is running, if not start it
$HADOOP_HOME/bin/hdfs dfsadmin -report 2>/dev/null | head -3
if [ $? -ne 0 ]; then
    echo "NameNode not responding, restarting..."
    $HADOOP_HOME/bin/hdfs --daemon start namenode 2>&1
    $HADOOP_HOME/bin/hdfs --daemon start datanode 2>&1
    sleep 3
fi

# Start HMS
echo "=== Starting HMS ==="
nohup $HIVE_HOME/bin/hive --service metastore -p 9083 > /tmp/hadoop-logs/metastore.log 2>&1 &
echo "HMS PID: $!"
sleep 5
netstat -tlnp 2>/dev/null | grep 9083
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/restart_arm_hms.sh'],
    input=hms_script, text=True, capture_output=True, timeout=10
)

r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/restart_arm_hms.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip()[:1500])
print("STDERR:", r2.stderr.strip()[:300] if r2.stderr else '')

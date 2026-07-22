import subprocess

script = """export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

if [ ! -f /tmp/hadoop-root/dfs/name/current/VERSION ]; then
    echo "Formatting NameNode..."
    $HADOOP_HOME/bin/hdfs namenode -format -force 2>&1 | tail -3
fi

echo "Starting NameNode..."
$HADOOP_HOME/bin/hdfs --daemon start namenode 2>&1
sleep 2

echo "Starting DataNode..."
$HADOOP_HOME/bin/hdfs --daemon start datanode 2>&1
sleep 2

echo "---"
jps 2>/dev/null || ps aux | grep java | grep -v grep
echo "---DONE---"
"""

# Write script to 211
r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/start_arm_hdfs.sh'],
    input=script, text=True, capture_output=True, timeout=10
)

# Execute via sshpass on container
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/start_arm_hdfs.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip())
print("STDERR:", r2.stderr.strip()[:500] if r2.stderr else '')

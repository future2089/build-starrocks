import subprocess

# Start Hive Metastore
script = """export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

# Check if metastore schema exists, init if needed
echo "Checking metastore schema..."
$HIVE_HOME/bin/schematool -dbType postgres -info 2>&1 | tail -5

# Start metastore in background
echo "Starting Hive Metastore on port 9083..."
nohup $HIVE_HOME/bin/hive --service metastore -p 9083 > /tmp/hadoop-logs/metastore.log 2>&1 &
echo "Metastore PID: $!"
sleep 3

# Verify
echo "---"
netstat -tlnp 2>/dev/null | grep 9083
echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/start_arm_hms.sh'],
    input=script, text=True, capture_output=True, timeout=10
)

r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/start_arm_hms.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip()[:2000])
print("STDERR:", r2.stderr.strip()[:500] if r2.stderr else '')

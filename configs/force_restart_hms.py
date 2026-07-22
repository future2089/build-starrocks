import subprocess

# Kill existing HMS on 9083 and restart
script = """export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

# Find and kill processes holding 9083
echo "=== Processes on 9083 ==="
fuser 9083/tcp 2>/dev/null || ss -tlnp | grep 9083 || netstat -tlnp 2>/dev/null | grep 9083

# Kill any existing HMS
echo "Killing existing HMS..."
ps aux | grep metastore | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2

# Restart HMS
echo "Starting HMS..."
nohup $HIVE_HOME/bin/hive --service metastore -p 9083 > /tmp/hadoop-logs/metastore.log 2>&1 &
echo "HMS PID: $!"
sleep 8
netstat -tlnp 2>/dev/null | grep 9083
echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/kill_restart_hms.sh'],
    input=script, text=True, capture_output=True, timeout=10
)

r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/kill_restart_hms.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip()[:1500] or '(empty)')
print(r2.stderr.strip()[:300] if r2.stderr else '')

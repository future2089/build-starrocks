import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

echo "1. Starting HMS with HIVE_CONF_DIR=/tmp/hive-conf"
HIVE_CONF_DIR=/tmp/hive-conf nohup $HIVE_HOME/bin/hive --service metastore -p 9083 > /tmp/hadoop-logs/metastore.log 2>&1 &
echo "HMS PID: $!"
sleep 15

echo "2. Check port"
netstat -tlnp 2>/dev/null | grep 9083

echo "3. Check log tail"
tail -10 /tmp/hadoop-logs/metastore.log

echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/start_hms_fixed.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/start_hms_fixed.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH
export HIVE_CONF_DIR=/tmp/hive-conf

echo "1. Kill old container HMS processes"
for pid in $(ps aux | grep "[d]ata/package/apache-hive" | awk '{print $2}'); do
  kill -9 $pid 2>/dev/null
  echo "Killed PID $pid"
done
sleep 2
rm -rf /tmp/hive-conf /tmp/metastore

echo "2. Create new config directory"
mkdir -p /tmp/hive-conf

echo "3. Copy and modify hive-site.xml for port 9084"
cp $HIVE_HOME/conf/hive-site.xml /tmp/hive-conf/hive-site.xml
sed -i 's|/var/hive/metastore|/tmp/metastore|g' /tmp/hive-conf/hive-site.xml
sed -i 's|9083|9084|g' /tmp/hive-conf/hive-site.xml

echo "4. Init schema with new config"
cd /tmp
$HIVE_HOME/bin/schematool -dbType derby -initSchema 2>&1 | tail -3

echo "5. Start HMS on port 9084"
nohup $HIVE_HOME/bin/hive --service metastore -p 9084 > /tmp/hadoop-logs/metastore-9084.log 2>&1 &
echo "HMS PID: $!"
sleep 15

echo "6. Verify port"
netstat -tlnp 2>/dev/null | grep 9084 || ss -tlnp 2>/dev/null | grep 9084 || echo "PORT NOT LISTENING"

echo "7. Check log"
tail -10 /tmp/hadoop-logs/metastore-9084.log

echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/setup_hms_9084.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/setup_hms_9084.sh'],
    capture_output=True, text=True, timeout=120
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

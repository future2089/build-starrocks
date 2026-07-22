import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

echo "1. Copy and modify hive-site.xml to use /tmp/metastore"
cp $HIVE_HOME/conf/hive-site.xml /tmp/hive-site.xml
# Replace the derby path
sed -i 's|/var/hive/metastore|/tmp/metastore|g' /tmp/hive-site.xml
cp /tmp/hive-site.xml $HIVE_HOME/conf/hive-site.xml

echo "2. Init schema"
cd /tmp
$HIVE_HOME/bin/schematool -dbType derby -initSchema 2>&1 | tail -10

echo "3. Check /tmp/metastore"
ls -la /tmp/metastore/ 2>/dev/null

echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/derby_fix.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/derby_fix.sh'],
    capture_output=True, text=True, timeout=30
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

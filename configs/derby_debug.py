import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HIVE_CONF_DIR=/tmp/hive-conf
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

rm -f /derby.log
rm -rf /tmp/metastore
mkdir -p /tmp/metastore

cd /tmp
$HIVE_HOME/bin/schematool -dbType derby -initSchema --verbose 2>&1 | tail -50

echo "=== DERBY.LOG ==="
cat /derby.log 2>/dev/null
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/derby_debug.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/derby_debug.sh'],
    capture_output=True, text=True, timeout=30
)
print(r2.stdout.strip()[:3000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

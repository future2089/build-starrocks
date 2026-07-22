import subprocess

# Start HDFS and Hive Metastore on 181
start_cmd = """
set -e
docker exec hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

# Start HDFS
echo "Starting HDFS..."
$HADOOP_HOME/sbin/start-dfs.sh

# Wait for HDFS
sleep 5

# Start Hive Metastore in background
echo "Starting Hive Metastore..."
nohup $HIVE_HOME/bin/hive --service metastore > /tmp/hive_metastore.log 2>&1 &
sleep 5

# Check processes
echo "--- Processes ---"
ps aux | grep -E "NameNode|DataNode|RunJar|HiveMeta" | grep -v grep

echo "--- Ports ---"
ss -tlnp | grep -E "8020|9083|9866|50070"
'
"""

r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 '%s' 2>&1" % start_cmd,
    shell=True, capture_output=True, text=True, timeout=120
)
print(r.stdout.strip()[:3000])
print('STDERR:', r.stderr.strip()[:500] if r.stderr else '')

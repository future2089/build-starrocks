#!/bin/bash
set -x

docker exec hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

ls -la $HADOOP_HOME/sbin/start-dfs.sh
ls -la $HIVE_HOME/bin/hive

if [ ! -d /tmp/hadoop/name/current ]; then
    echo "Formatting HDFS NameNode..."
    $HADOOP_HOME/bin/hdfs namenode -format -force
fi

echo "Starting HDFS..."
$HADOOP_HOME/sbin/start-dfs.sh

sleep 10

echo "Starting Hive Metastore..."
nohup $HIVE_HOME/bin/hive --service metastore > /tmp/hive_metastore.log 2>&1 &

sleep 5

echo "--- Processes ---"
ps aux | grep -E "NameNode|DataNode|HiveMeta" | grep -v grep

echo "--- Ports ---"
ss -tlnp | grep -E "8020|9083|9866|50070" || true
'

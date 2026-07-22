#!/bin/bash
set -x

docker exec hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

# Format if needed
if [ ! -d /tmp/hadoop/name/current ]; then
    echo "Formatting HDFS NameNode..."
    $HADOOP_HOME/bin/hdfs namenode -format -force
fi

# Start NameNode directly
nohup $HADOOP_HOME/bin/hdfs namenode > /tmp/namenode.log 2>&1 &
sleep 5

# Start DataNode directly
nohup $HADOOP_HOME/bin/hdfs datanode > /tmp/datanode.log 2>&1 &
sleep 5

echo "--- Processes ---"
ps aux | grep -E "NameNode|DataNode" | grep -v grep

echo "--- Ports ---"
netstat -tlnp 2>/dev/null | grep -E "8020|9866|50070" || true
'

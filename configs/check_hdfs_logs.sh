#!/bin/bash
set -x

docker exec hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

echo "--- NameNode log ---"
cat /tmp/namenode.log 2>/dev/null | tail -30

echo "--- DataNode log ---"
cat /tmp/datanode.log 2>/dev/null | tail -30

echo "--- Java version ---"
java -version 2>&1 | head -3

echo "--- HDFS version ---"
$HADOOP_HOME/bin/hdfs version 2>&1 | head -5
'

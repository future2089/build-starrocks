#!/bin/bash

docker exec hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

echo "Testing hive command..."
$HIVE_HOME/bin/hive --help 2>&1 | head -5

echo "Starting HMS in foreground for 10s to capture errors..."
timeout 15 $HIVE_HOME/bin/hive --service metastore 2>&1 | tail -50
' 2>&1

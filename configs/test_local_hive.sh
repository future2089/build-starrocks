#!/bin/bash

docker exec hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HIVE_LOG_DIR=/tmp/hive-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

# Try to list databases using local HMS
$HIVE_HOME/bin/beeline -u "jdbc:hive2://127.0.0.1:9083/default" -e "show databases;" 2>&1 | tail -20

echo "--- Try thrift direct connection ---"
$HIVE_HOME/bin/hive --hiveconf hive.metastore.uris=thrift://127.0.0.1:9083 -e "show databases;" 2>&1 | tail -20
' 2>&1

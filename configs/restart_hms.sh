#!/bin/bash

docker exec hadoop-arm bash -c '
# Kill existing HMS
pkill -f HiveMetaStore || true
sleep 3

# Restart HMS with writable log dir and correct env
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

mkdir -p /tmp/hadoop-logs

nohup $HIVE_HOME/bin/hive --service metastore > /tmp/hive_metastore.log 2>&1 &

echo "Waiting for HMS to start..."
for i in $(seq 1 30); do
    if grep -E ":237B " /proc/net/tcp >/dev/null 2>&1; then
        echo "HMS listening on 9083 after ${i}s"
        break
    fi
    sleep 1
done

echo "--- HMS process ---"
ps aux | grep HiveMetaStore | grep -v grep

echo "--- HMS log tail ---"
cat /tmp/hive_metastore.log | tail -50
'

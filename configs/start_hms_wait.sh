#!/bin/bash

docker exec hadoop-arm bash -c '
# Make sure old HMS is killed
pkill -f HiveMetaStore || true
sleep 3

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HIVE_LOG_DIR=/tmp/hive-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

mkdir -p /tmp/hive-logs /tmp/hadoop-logs

echo "Starting HMS in background..."
nohup $HIVE_HOME/bin/hive --service metastore > /tmp/hive_metastore.log 2>&1 &
HMS_PID=$!
echo "HMS PID: $HMS_PID"

echo "Waiting for HMS to listen on 9083..."
for i in $(seq 1 60); do
    if grep -E ":237B " /proc/net/tcp >/dev/null 2>&1; then
        echo "HMS listening on 9083 after ${i}s"
        break
    fi
    if ! kill -0 $HMS_PID 2>/dev/null; then
        echo "HMS process died after ${i}s"
        break
    fi
    sleep 1
done

echo "--- Process ---"
ps aux | grep HiveMetaStore | grep -v grep

echo "--- Log tail ---"
cat /tmp/hive_metastore.log | tail -80

echo "--- Port ---"
grep -E ":237B " /proc/net/tcp | head -1 || echo "NOT LISTENING"
'

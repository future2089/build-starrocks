#!/bin/bash

# Kill any existing HMS in container
docker exec hadoop-arm bash -c 'pkill -f HiveMetaStore || true; sleep 2; rm -f /tmp/hive_metastore.log'

# Start HMS detached
docker exec -d hadoop-arm bash -c '
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/data/package/hadoop-3.3.6
export HIVE_HOME=/data/package/apache-hive-3.1.3-bin
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HIVE_LOG_DIR=/tmp/hive-logs
export PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH
mkdir -p /tmp/hive-logs /tmp/hadoop-logs
nohup $HIVE_HOME/bin/hive --service metastore > /tmp/hive_metastore.log 2>&1 &
'

sleep 2

echo "HMS process:"
docker exec hadoop-arm bash -c 'ps aux | grep HiveMetaStore | grep -v grep'

echo "Waiting for port 9083..."
for i in $(seq 1 60); do
    if docker exec hadoop-arm bash -c 'grep -E ":237B " /proc/net/tcp >/dev/null 2>&1'; then
        echo "HMS listening on 9083 after ${i}s"
        break
    fi
    sleep 1
done

echo "Final port check:"
docker exec hadoop-arm bash -c 'grep -E ":237B " /proc/net/tcp | head -1 || echo NOT LISTENING'

echo "Log tail:"
docker exec hadoop-arm bash -c 'cat /tmp/hive_metastore.log | tail -50'

#!/bin/bash

docker exec hadoop-arm bash -c '
echo "--- Hive Metastore log ---"
cat /tmp/hive_metastore.log 2>/dev/null | tail -50

echo "--- DataNode log ---"
cat /tmp/hadoop-logs/datanode.log 2>/dev/null | tail -50

echo "--- NameNode log tail ---"
cat /tmp/hadoop-logs/namenode.log 2>/dev/null | tail -30

echo "--- All listening ports (hex) ---"
for port in 8020 9083 9866 50070; do
    hex=$(printf "%04X" $port)
    found=$(grep -E ":$hex " /proc/net/tcp 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        echo "Port $port (0x$hex): LISTENING"
    else
        echo "Port $port (0x$hex): NOT listening"
    fi
done

echo "--- Processes ---"
ps aux | grep -E "NameNode|DataNode|HiveMeta" | grep -v grep
'

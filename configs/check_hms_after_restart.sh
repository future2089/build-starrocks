#!/bin/bash

docker exec hadoop-arm bash -c '
ps aux | grep HiveMetaStore | grep -v grep

echo "=== log tail ==="
cat /tmp/hive_metastore.log | tail -50

echo "=== port check ==="
grep -E ":237B " /proc/net/tcp | head -1 || echo "NOT LISTENING"
'

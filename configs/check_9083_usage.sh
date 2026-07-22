#!/bin/bash

docker exec hadoop-arm bash -c '
# Check actual hive-site.xml values
cat /data/package/apache-hive-3.1.3-bin/conf/hive-site.xml | grep -E "metastore.uris|metastore.port|thrift.bind"

# Check if 9083 is in use by any process
echo "--- Processes using port 9083 ---"
for pid in $(ls /proc | grep -E "^[0-9]+$"); do
    if grep -E ":237B " /proc/$pid/net/tcp >/dev/null 2>&1; then
        echo "PID $pid"
        cat /proc/$pid/cmdline 2>/dev/null | tr "\\0" " " | head -c 200
        echo
    fi
done
'

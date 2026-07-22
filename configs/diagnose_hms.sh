#!/bin/bash

docker exec hadoop-arm bash -c '
# Check if HMS is still running and consuming CPU
ps aux | grep HiveMetaStore | grep -v grep

echo "--- log files ---"
ls -la /tmp/hive-logs/ 2>/dev/null || true
ls -la /tmp/hadoop-logs/ 2>/dev/null || true
ls -la /var/log/hive/ 2>/dev/null || true
find /tmp -name "hive*.log" -mmin -5 2>/dev/null | head -5

echo "--- hive log ---"
find /tmp -name "hive*.log" -mmin -5 2>/dev/null | head -1 | xargs -I {} cat {} 2>/dev/null | tail -50

echo "--- jstack ---"
PID=$(ps aux | grep HiveMetaStore | grep -v grep | awk "{print \$2}" | head -1)
if [ -n "$PID" ]; then
    echo "HMS PID: $PID"
    $JAVA_HOME/bin/jstack $PID 2>/dev/null | head -50 || true
fi
'

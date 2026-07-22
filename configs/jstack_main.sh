#!/bin/bash

docker exec hadoop-arm bash -c '
PID=$(ps aux | grep HiveMetaStore | grep -v grep | awk "{print \$2}" | head -1)
if [ -n "$PID" ]; then
    $JAVA_HOME/bin/jstack $PID 2>/dev/null | grep -A 20 "main\"" | head -40
fi
'

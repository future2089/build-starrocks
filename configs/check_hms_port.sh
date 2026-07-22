#!/bin/bash

docker exec hadoop-arm bash -c '
PID=$(ps aux | grep HiveMetaStore | grep -v grep | awk "{print \$2}" | head -1)
echo "HMS PID: $PID"
if [ -n "$PID" ]; then
    echo "--- /proc/PID/net/tcp ---"
    grep -E "0A 00000000:0000" /proc/$PID/net/tcp | head -10
    echo "--- All listening ports for HMS ---"
    awk "/^ *[0-9]+: / {split(\$2,a,\":\"); if (a[2] != \"0000\" && \$4 == \"0A\") print \$0}" /proc/$PID/net/tcp | head -20
fi

echo "--- Host /proc/net/tcp ---"
grep -E "0A 00000000:0000" /proc/net/tcp | head -10
'

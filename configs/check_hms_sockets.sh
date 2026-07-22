#!/bin/bash

docker exec hadoop-arm bash -c '
PID=$(ps aux | grep HiveMetaStore | grep -v grep | awk "{print \$2}" | head -1)
echo "HMS PID: $PID"

# Check all possible sockets
for f in /proc/$PID/net/tcp /proc/$PID/net/tcp6 /proc/$PID/net/udp /proc/$PID/net/udp6; do
    if [ -f "$f" ]; then
        echo "--- $f ---"
        cat "$f" | head -5
    fi
done

# Check using lsof
which lsof >/dev/null 2>&1 && lsof -p $PID -nP | grep LISTEN || echo "lsof not available"

# Check using /proc/PID/fd
ls -la /proc/$PID/fd 2>/dev/null | grep socket | head -10
'

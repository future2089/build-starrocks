#!/bin/bash

docker exec hadoop-arm bash -c '
echo "--- netstat ---"
netstat -tlnp 2>/dev/null | grep -E "8020|9866|50070|9083" || true

echo "--- ss ---"
which ss 2>/dev/null || echo "ss not found"

echo "--- /proc/net/tcp ---"
grep -E ":1F54|:2682|:138E|:13AE" /proc/net/tcp 2>/dev/null || true

# Convert: 8020=0x1F54, 9866=0x2682, 50070=0x138E, 9083=0x138E wait 9083=0x237B
# 9083 = 0x237B
# 8020 = 0x1F54
# 9866 = 0x2682
# 50070 = 0x138E
echo "--- Port hex checks ---"
grep -E ":237B|:1F54|:2682" /proc/net/tcp 2>/dev/null || true
'

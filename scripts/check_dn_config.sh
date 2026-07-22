#!/bin/bash
set -e
HOST_181="root@192.168.0.181"

ssh $HOST_181 docker exec hadoop-arm jar xf /data/package/hadoop-3.3.6/share/hadoop/hdfs/hadoop-hdfs-3.3.6.jar org/apache/hadoop/hdfs/server/datanode/DataNode.class

ssh $HOST_181 docker exec hadoop-arm javap -c -p DataNode.class 2>&1 | grep -A 50 "checkSecureConfig" | head -60

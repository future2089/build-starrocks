#!/bin/bash
HOST_181="root@192.168.0.181"

ssh $HOST_181 docker exec hadoop-arm bash -c 'kill -9 3276 2>/dev/null; sleep 1'
ssh $HOST_181 docker exec hadoop-arm bash -c 'rm -f /tmp/hadoop-root-namenode.pid /tmp/hadoop-root-datanode.pid'
ssh $HOST_181 docker exec hadoop-arm kinit -kt /etc/hdfs.keytab hdfs/arm-ha@ARM.SR.TEST
echo "kinit OK"

ssh $HOST_181 docker exec -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/hadoop-3.3.6/bin/hdfs --daemon start namenode 2>&1
echo "NN started"

sleep 3
ssh $HOST_181 docker exec -d -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/hadoop-3.3.6/bin/hdfs datanode 2>&1
echo "DN starting..."

sleep 3
ssh $HOST_181 docker exec hadoop-arm ps aux | grep -E "[n]amenode|[d]atanode"

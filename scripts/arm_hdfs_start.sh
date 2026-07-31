#!/bin/bash
# Run on 211 to start HDFS on 181's hadoop-arm container

ssh root@192.168.0.181 bash -c '
set -e
HADOOP_HOME=/data/package/hadoop-3.3.6
HADOOP_LOG_DIR=/var/log/hadoop

# 1. Copy new hdfs-site.xml
cp /tmp/arm-hdfs-site-v2.xml $HADOOP_HOME/etc/hadoop/hdfs-site.xml

# 2. Restart NameNode (kill old, start new)
PID=$(cat $HADOOP_LOG_DIR/hadoop-root-namenode-host181.pid 2>/dev/null || true)
if [ -n "$PID" ]; then
  kill $PID 2>/dev/null || true
  sleep 2
fi

# 3. kinit
kinit -kt /etc/hdfs.keytab hdfs/arm-ha@ARM.SR.TEST

# 4. Start NameNode
env HADOOP_LOG_DIR=$HADOOP_LOG_DIR HADOOP_HOME=$HADOOP_HOME $HADOOP_HOME/bin/hdfs --daemon start namenode
echo "NameNode started"

# 5. Start DataNode
env HADOOP_LOG_DIR=$HADOOP_LOG_DIR HADOOP_HOME=$HADOOP_HOME $HADOOP_HOME/bin/hdfs --daemon start datanode
echo "DataNode started"

# 6. Verify
sleep 3
ps aux | grep -E "namenode|datanode" | grep -v grep
'

#!/bin/bash
set -e
HOST_181="root@192.168.0.181"

# Step 1: Rewrite hdfs-site.xml cleanly
echo "=== Rewriting hdfs-site.xml ==="
cat > /tmp/hdfs-site-clean.xml << 'XMLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
<property><name>dfs.replication</name><value>1</value></property>
<property><name>dfs.namenode.name.dir</name><value>/tmp/hadoop/name</value></property>
<property><name>dfs.datanode.data.dir</name><value>/tmp/hadoop/data</value></property>
<property><name>dfs.namenode.http.address</name><value>0.0.0.0:50070</value></property>
<property><name>dfs.datanode.hostname</name><value>192.168.0.181</value></property>
<property><name>dfs.permissions</name><value>false</value></property>
<property><name>dfs.nameservices</name><value>arm-ha</value></property>
<property><name>dfs.ha.namenodes.arm-ha</name><value>nn1</value></property>
<property><name>dfs.namenode.rpc-address.arm-ha.nn1</name><value>0.0.0.0:8020</value></property>
<property><name>dfs.namenode.http-address.arm-ha.nn1</name><value>0.0.0.0:50070</value></property>
<property><name>dfs.client.failover.proxy.provider.arm-ha</name><value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value></property>
<property><name>dfs.namenode.keytab.file</name><value>/etc/hdfs.keytab</value></property>
<property><name>dfs.namenode.kerberos.principal</name><value>hdfs/arm-ha@ARM.SR.TEST</value></property>
<property><name>dfs.datanode.keytab.file</name><value>/etc/hdfs.keytab</value></property>
<property><name>dfs.datanode.kerberos.principal</name><value>hdfs/arm-ha@ARM.SR.TEST</value></property>
<property><name>dfs.data.transfer.protection</name><value>authentication</value></property>
<property><name>dfs.block.access.token.enable</name><value>true</value></property>
<property><name>dfs.datanode.address</name><value>0.0.0.0:9866</value></property>
<property><name>dfs.datanode.http.address</name><value>0.0.0.0:9864</value></property>
<property><name>dfs.datanode.https.address</name><value>0.0.0.0:9865</value></property>
<property><name>dfs.datanode.sasl.embedded.http.server</name><value>true</value></property>
</configuration>
XMLEOF

scp /tmp/hdfs-site-clean.xml $HOST_181:/tmp/hdfs-site-clean.xml
ssh $HOST_181 cp /tmp/hdfs-site-clean.xml /data/package/hadoop-3.3.6/etc/hadoop/hdfs-site.xml

# Step 2: Remove old log files
echo "=== Cleaning logs ==="
ssh $HOST_181 docker exec hadoop-arm rm -f /var/log/hadoop/hadoop-root-datanode-host181.log
ssh $HOST_181 docker exec hadoop-arm rm -f /var/log/hadoop/hadoop-root-datanode-host181.out
ssh $HOST_181 docker exec hadoop-arm rm -f /tmp/hadoop-root-datanode.pid
ssh $HOST_181 docker exec hadoop-arm rm -f /tmp/hadoop-root-namenode.pid

# Step 3: Kill old NN and DN
echo "=== Killing old processes ==="
ssh $HOST_181 docker exec hadoop-arm bash -c 'ps aux | grep -E "[n]amenode|[d]atanode" | awk "{print \$2}" | xargs -r kill; sleep 2; echo old_killed'

# Step 4: kinit
echo "=== kinit ==="
ssh $HOST_181 docker exec hadoop-arm kinit -kt /etc/hdfs.keytab hdfs/arm-ha@ARM.SR.TEST
echo "kinit OK"

# Step 5: Format NN (if not already formatted)
echo "=== Formatting NN ==="
ssh $HOST_181 docker exec -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/hadoop-3.3.6/bin/hdfs namenode -format -force 2>&1 | tail -3
echo "format OK"

# Step 6: Start NN
echo "=== Starting NameNode ==="
ssh $HOST_181 docker exec -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/hadoop-3.3.6/bin/hdfs --daemon start namenode 2>&1
sleep 3

# Step 7: Start DN in foreground (bg via docker detach)
echo "=== Starting DataNode ==="
ssh $HOST_181 docker exec -d -e HADOOP_LOG_DIR=/var/log/hadoop hadoop-arm /data/package/hadoop-3.3.6/bin/hdfs datanode 2>&1
sleep 3

# Step 8: Verify
echo "=== Verification ==="
ssh $HOST_181 docker exec hadoop-arm ps aux | grep -E "[n]amenode|[d]atanode" | grep -v grep

echo "=== HDFS Setup Complete ==="

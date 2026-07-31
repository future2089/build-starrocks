#!/bin/bash
set -e
HOST_IP=192.168.0.181
HADOOP_HOME=/data/hadoop-3.3.6
HIVE_HOME=/data/apache-hive-3.1.3-bin
JAVA_HOME=/usr/lib/jvm/java-1.8.0

# ====== HDFS Configuration ======
mkdir -p /tmp/hadoop/name /tmp/hadoop/data

cat > $HADOOP_HOME/etc/hadoop/core-site.xml << 'XML'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
<property><name>fs.defaultFS</name><value>hdfs://arm-ha</value></property>
<property><name>hadoop.tmp.dir</name><value>/tmp/hadoop</value></property>
<property><name>hadoop.security.authentication</name><value>kerberos</value></property>
<property><name>hadoop.security.authorization</name><value>true</value></property>
<property><name>ipc.client.fallback-to-simple-auth-allowed</name><value>true</value></property>
<property><name>hadoop.proxyuser.root.hosts</name><value>*</value></property>
<property><name>hadoop.proxyuser.root.groups</name><value>*</value></property>
</configuration>
XML

cat > $HADOOP_HOME/etc/hadoop/hdfs-site.xml << 'XML'
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
<property><name>dfs.namenode.rpc-address.arm-ha.nn1</name><value>192.168.0.181:8020</value></property>
<property><name>dfs.namenode.http-address.arm-ha.nn1</name><value>192.168.0.181:50070</value></property>
<property><name>dfs.client.failover.proxy.provider.arm-ha</name><value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value></property>
<property><name>dfs.namenode.keytab.file</name><value>/etc/hdfs.keytab</value></property>
<property><name>dfs.namenode.kerberos.principal</name><value>hdfs/arm-ha@ARM.SR.TEST</value></property>
<property><name>dfs.datanode.keytab.file</name><value>/etc/hdfs.keytab</value></property>
<property><name>dfs.datanode.kerberos.principal</name><value>hdfs/arm-ha@ARM.SR.TEST</value></property>
<property><name>dfs.data.transfer.protection</name><value>authentication</value></property>
<property><name>dfs.block.access.token.enable</name><value>true</value></property>
</configuration>
XML

# Format HDFS
export JAVA_HOME=$JAVA_HOME
export HADOOP_HOME=$HADOOP_HOME
$HADOOP_HOME/bin/hdfs namenode -format -force 2>&1 | tail -3

# Start HDFS with Kerberos
$HADOOP_HOME/sbin/hadoop-daemon.sh start namenode
$HADOOP_HOME/sbin/hadoop-daemon.sh start datanode
sleep 3

# Verify HDFS
$HADOOP_HOME/bin/hdfs dfsadmin -report 2>&1 | head -10

# ====== Hive Metastore Configuration ======

# Start MySQL
mysqld_safe &
sleep 3
mysql -u root -e "
  CREATE DATABASE IF NOT EXISTS hive_metastore;
  CREATE USER IF NOT EXISTS 'hive'@'localhost' IDENTIFIED BY 'hive';
  GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'localhost';
  FLUSH PRIVILEGES;
" 2>&1

# Configure Hive
cat > $HIVE_HOME/conf/hive-site.xml << 'XML'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
<property><name>javax.jdo.option.ConnectionURL</name><value>jdbc:mysql://localhost:3306/hive_metastore?createDatabaseIfNotExist=true</value></property>
<property><name>javax.jdo.option.ConnectionDriverName</name><value>com.mysql.jdbc.Driver</value></property>
<property><name>javax.jdo.option.ConnectionUserName</name><value>hive</value></property>
<property><name>javax.jdo.option.ConnectionPassword</name><value>hive</value></property>
<property><name>hive.metastore.uris</name><value>thrift://192.168.0.181:9083</value></property>
<property><name>hive.metastore.kerberos.principal</name><value>hive/arm-hive@ARM.SR.TEST</value></property>
<property><name>hive.metastore.kerberos.keytab.file</name><value>/etc/hive.keytab</value></property>
<property><name>hive.metastore.sasl.enabled</name><value>true</value></property>
<property><name>hive.metastore.warehouse.dir</name><value>hdfs://arm-ha/user/hive/warehouse</value></property>
</configuration>
XML

# Create JAAS config
cat > /tmp/hive_jaas.conf << 'JAAS'
HiveServer2 {
  com.sun.security.auth.module.Krb5LoginModule required
  useKeyTab=true
  keyTab="/etc/hive.keytab"
  principal="hive/arm-hive@ARM.SR.TEST"
  storeKey=true
  useTicketCache=false;
};
Client {
  com.sun.security.auth.module.Krb5LoginModule required
  useKeyTab=true
  keyTab="/etc/hive.keytab"
  principal="hive/arm-hive@ARM.SR.TEST"
  storeKey=true
  useTicketCache=false;
};
JAAS

# Copy MySQL JDBC driver
if [ ! -f $HIVE_HOME/lib/mysql-connector-java.jar ]; then
  find /data -name "mysql-connector-java*.jar" -exec cp {} $HIVE_HOME/lib/ \; 2>/dev/null || true
  find /root -name "mysql-connector-java*.jar" -exec cp {} $HIVE_HOME/lib/ \; 2>/dev/null || true
fi

# Initialize Hive schema
$HIVE_HOME/bin/schematool -dbType mysql -initSchema 2>&1 | tail -5

# Start HMS with Kerberos
HADOOP_OPTS="-Djava.security.krb5.conf=/etc/krb5.conf -Djava.security.auth.login.config=/tmp/hive_jaas.conf" \
$HIVE_HOME/bin/hive --service metastore -p 9083 2>&1 &
sleep 5

echo "=== HDFS + HMS Setup Complete ==="
echo "HDFS: hdfs://arm-ha (192.168.0.181:8020)"
echo "HMS: thrift://192.168.0.181:9083 (Kerberos)"
echo "Keytabs: /etc/hdfs.keytab, /etc/hive.keytab"

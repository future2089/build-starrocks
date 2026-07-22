#!/bin/bash
# Setup HDFS (simplified HA) + Hive Metastore container on 181
set -e

HOST_IP=$(hostname -I | awk '{print $1}')
echo "Host IP: $HOST_IP"

# Stop existing container
docker rm -f hadoop-arm 2>/dev/null || true

# Start container with bind mounts
docker run -d --name hadoop-arm \
  --network host \
  --restart unless-stopped \
  -v /data:/data:ro \
  -v /data/keytabs:/etc/security/keytabs \
  openeuler/openeuler:22.03 sleep infinity

# Install required packages
docker exec hadoop-arm dnf install -y \
  mysql-server \
  krb5-libs krb5-workstation \
  procps-ng \
  openssh-clients \
  2>&1 | tail -3

# Copy Hadoop and Hive config templates
HADOOP_HOME=/data/hadoop-3.3.6
HIVE_HOME=/data/apache-hive-3.1.3-bin

# Create krb5.conf inside container
cat > /tmp/krb5_arm.conf << 'KRBCONF'
[logging]
 default = FILE:/var/log/krb5libs.log
 kdc = FILE:/var/log/krb5kdc.log
 admin_server = FILE:/var/log/kadmind.log

[libdefaults]
 dns_lookup_realm = false
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true
 rdns = false
 default_realm = ARM.SR.TEST
 default_ccache_name = FILE:/tmp/krb5cc_%{uid}

[realms]
 ARM.SR.TEST = {
  kdc = 192.168.0.181:88
  admin_server = 192.168.0.181:749
  default_domain = arm.sr.test
 }

[domain_realm]
 .arm.sr.test = ARM.SR.TEST
 arm.sr.test = ARM.SR.TEST
KRBCONF

docker cp /tmp/krb5_arm.conf hadoop-arm:/etc/krb5.conf

# ============== Configure HDFS ==============

CORE_SITE="$HADOOP_HOME/etc/hadoop/core-site.xml"
HDFS_SITE="$HADOOP_HOME/etc/hadoop/hdfs-site.xml"

# Create core-site.xml
docker exec hadoop-arm bash -c "cat > $CORE_SITE << 'XML'
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://arm-ha</value>
  </property>
  <property>
    <name>hadoop.tmp.dir</name>
    <value>/tmp/hadoop</value>
  </property>
  <property>
    <name>hadoop.security.authentication</name>
    <value>kerberos</value>
  </property>
  <property>
    <name>hadoop.security.authorization</name>
    <value>true</value>
  </property>
  <property>
    <name>ipc.client.fallback-to-simple-auth-allowed</name>
    <value>true</value>
  </property>
  <property>
    <name>hadoop.proxyuser.root.hosts</name>
    <value>*</value>
  </property>
  <property>
    <name>hadoop.proxyuser.root.groups</name>
    <value>*</value>
  </property>
</configuration>
XML"

# Create hdfs-site.xml with simplified HA
docker exec hadoop-arm bash -c "cat > $HDFS_SITE << 'XML'
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>/tmp/hadoop/name</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/tmp/hadoop/data</value>
  </property>
  <property>
    <name>dfs.namenode.http.address</name>
    <value>0.0.0.0:50070</value>
  </property>
  <property>
    <name>dfs.datanode.hostname</name>
    <value>$HOST_IP</value>
  </property>
  <property>
    <name>dfs.permissions</name>
    <value>false</value>
  </property>
  <!-- HA nameservice configuration -->
  <property>
    <name>dfs.nameservices</name>
    <value>arm-ha</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.arm-ha</name>
    <value>nn1</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.arm-ha.nn1</name>
    <value>$HOST_IP:8020</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.arm-ha.nn1</name>
    <value>$HOST_IP:50070</value>
  </property>
  <property>
    <name>dfs.client.failover.proxy.provider.arm-ha</name>
    <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
  </property>
  <!-- Kerberos config -->
  <property>
    <name>dfs.namenode.keytab.file</name>
    <value>/etc/security/keytabs/hdfs.keytab</value>
  </property>
  <property>
    <name>dfs.namenode.kerberos.principal</name>
    <value>hdfs/arm-ha@ARM.SR.TEST</value>
  </property>
  <property>
    <name>dfs.datanode.keytab.file</name>
    <value>/etc/security/keytabs/hdfs.keytab</value>
  </property>
  <property>
    <name>dfs.datanode.kerberos.principal</name>
    <value>hdfs/arm-ha@ARM.SR.TEST</value>
  </property>
  <property>
    <name>dfs.data.transfer.protection</name>
    <value>authentication</value>
  </property>
  <property>
    <name>dfs.block.access.token.enable</name>
    <value>true</value>
  </property>
</configuration>
XML"

# Format HDFS
docker exec hadoop-arm bash -c "export HADOOP_HOME=$HADOOP_HOME && \
  export JAVA_HOME=/usr/lib/jvm/java-1.8.0 && \
  mkdir -p /tmp/hadoop && \
  $HADOOP_HOME/bin/hdfs namenode -format -force 2>&1 | tail -5"

# ============== Configure MySQL for HMS ==============

docker exec hadoop-arm bash -c "mysqld --initialize-insecure --user=root 2>&1 | tail -3" || true
docker exec -d hadoop-arm mysqld_safe
sleep 3
docker exec hadoop-arm mysql -u root -e "
  CREATE DATABASE IF NOT EXISTS hive_metastore;
  CREATE USER IF NOT EXISTS 'hive'@'localhost' IDENTIFIED BY 'hive';
  GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'localhost';
  FLUSH PRIVILEGES;
" 2>&1

# ============== Configure Hive Metastore ==============

HIVE_CONF="$HIVE_HOME/conf"
docker exec hadoop-arm mkdir -p $HIVE_CONF

# hive-site.xml
docker exec hadoop-arm bash -c "cat > $HIVE_CONF/hive-site.xml << 'XML'
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<configuration>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://localhost:3306/hive_metastore?createDatabaseIfNotExist=true</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.jdbc.Driver</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>hive</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>hive</value>
  </property>
  <property>
    <name>hive.metastore.uris</name>
    <value>thrift://$HOST_IP:9083</value>
  </property>
  <property>
    <name>hive.metastore.kerberos.principal</name>
    <value>hive/arm-hive@ARM.SR.TEST</value>
  </property>
  <property>
    <name>hive.metastore.kerberos.keytab.file</name>
    <value>/etc/security/keytabs/hive.keytab</value>
  </property>
  <property>
    <name>hive.metastore.sasl.enabled</name>
    <value>true</value>
  </property>
  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>hdfs://arm-ha/user/hive/warehouse</value>
  </property>
</configuration>
XML"

# Initialize Hive schema
docker exec hadoop-arm bash -c "export HADOOP_HOME=$HADOOP_HOME && \
  export JAVA_HOME=/usr/lib/jvm/java-1.8.0 && \
  export HADOOP_CLASSPATH=$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/* && \
  $HIVE_HOME/bin/schematool -dbType mysql -initSchema --verbose 2>&1 | tail -5"

echo "========================================="
echo "Setup complete!"
echo "Next steps:"
echo "  1. Start HDFS: docker exec hadoop-arm bash -c 'export HADOOP_HOME=$HADOOP_HOME && \$HADOOP_HOME/sbin/hadoop-daemon.sh start namenode && \$HADOOP_HOME/sbin/hadoop-daemon.sh start datanode'"
echo "  2. Start HMS:  docker exec hadoop-arm bash -c 'export HADOOP_HOME=$HADOOP_HOME && export JAVA_HOME=/usr/lib/jvm/java-1.8.0 && \$HIVE_HOME/bin/hive --service metastore'"
echo "========================================="

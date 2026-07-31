#!/usr/bin/env python3
import os

HADOOP_HOME = "/data/package/hadoop-3.3.6"
HOST_IP = "192.168.0.181"

os.makedirs(HADOOP_HOME + "/etc/hadoop", exist_ok=True)

# core-site.xml
core_site = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
<property><name>fs.defaultFS</name><value>hdfs://arm-ha</value></property>
<property><name>hadoop.tmp.dir</name><value>/tmp/hadoop</value></property>
<property><name>hadoop.security.authentication</name><value>kerberos</value></property>
<property><name>hadoop.security.authorization</name><value>true</value></property>
<property><name>ipc.client.fallback-to-simple-auth-allowed</name><value>true</value></property>
<property><name>hadoop.proxyuser.root.hosts</name><value>*</value></property>
<property><name>hadoop.proxyuser.root.groups</name><value>*</value></property>
</configuration>"""

with open(HADOOP_HOME + "/etc/hadoop/core-site.xml", "w") as f:
    f.write(core_site)
print("core-site.xml written")

# hdfs-site.xml
hdfs_site = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
<property><name>dfs.replication</name><value>1</value></property>
<property><name>dfs.namenode.name.dir</name><value>/tmp/hadoop/name</value></property>
<property><name>dfs.datanode.data.dir</name><value>/tmp/hadoop/data</value></property>
<property><name>dfs.namenode.http.address</name><value>0.0.0.0:50070</value></property>
<property><name>dfs.datanode.hostname</name><value>{HOST_IP}</value></property>
<property><name>dfs.permissions</name><value>false</value></property>
<property><name>dfs.nameservices</name><value>arm-ha</value></property>
<property><name>dfs.ha.namenodes.arm-ha</name><value>nn1</value></property>
<property><name>dfs.namenode.rpc-address.arm-ha.nn1</name><value>{HOST_IP}:8020</value></property>
<property><name>dfs.namenode.http-address.arm-ha.nn1</name><value>{HOST_IP}:50070</value></property>
<property><name>dfs.client.failover.proxy.provider.arm-ha</name><value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value></property>
<property><name>dfs.namenode.keytab.file</name><value>/etc/hdfs.keytab</value></property>
<property><name>dfs.namenode.kerberos.principal</name><value>hdfs/arm-ha@ARM.SR.TEST</value></property>
<property><name>dfs.datanode.keytab.file</name><value>/etc/hdfs.keytab</value></property>
<property><name>dfs.datanode.kerberos.principal</name><value>hdfs/arm-ha@ARM.SR.TEST</value></property>
<property><name>dfs.data.transfer.protection</name><value>authentication</value></property>
<property><name>dfs.block.access.token.enable</name><value>true</value></property>
</configuration>"""

with open(HADOOP_HOME + "/etc/hadoop/hdfs-site.xml", "w") as f:
    f.write(hdfs_site)
print("hdfs-site.xml written")

# hadoop-env.sh JAVA_HOME
env_line = '\nexport JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.462.b08-4.oe2403sp2.x86_64\n'
with open(HADOOP_HOME + "/etc/hadoop/hadoop-env.sh", "a") as f:
    f.write(env_line)
print("hadoop-env.sh updated")

# hive-site.xml
HIVE_HOME = "/data/package/apache-hive-3.1.3-bin"
os.makedirs(HIVE_HOME + "/conf", exist_ok=True)

hive_site = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
<property><name>javax.jdo.option.ConnectionURL</name><value>jdbc:mysql://localhost:3306/hive_metastore?createDatabaseIfNotExist=true</value></property>
<property><name>javax.jdo.option.ConnectionDriverName</name><value>com.mysql.jdbc.Driver</value></property>
<property><name>javax.jdo.option.ConnectionUserName</name><value>hive</value></property>
<property><name>javax.jdo.option.ConnectionPassword</name><value>hive</value></property>
<property><name>hive.metastore.uris</name><value>thrift://{HOST_IP}:9083</value></property>
<property><name>hive.metastore.kerberos.principal</name><value>hive/arm-hive@ARM.SR.TEST</value></property>
<property><name>hive.metastore.kerberos.keytab.file</name><value>/etc/hive.keytab</value></property>
<property><name>hive.metastore.sasl.enabled</name><value>true</value></property>
<property><name>hive.metastore.warehouse.dir</name><value>hdfs://arm-ha/user/hive/warehouse</value></property>
</configuration>"""

with open(HIVE_HOME + "/conf/hive-site.xml", "w") as f:
    f.write(hive_site)
print("hive-site.xml written")

# JAAS config
jaas = '''HiveServer2 {
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
'''

with open("/tmp/hive_jaas.conf", "w") as f:
    f.write(jaas)
print("JAAS config written")

print("=== All config files written successfully ===")

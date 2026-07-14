import os

base = '/data/starrocks-deploy'

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f'Wrote {path}')

# ====== Cluster A ======

# core-site.xml for cluster_a
write_file(f'{base}/cluster_a/conf/core-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://nameservice_a</value>
  </property>
  <property>
    <name>hadoop.security.authentication</name>
    <value>kerberos</value>
  </property>
  <property>
    <name>hadoop.security.authorization</name>
    <value>true</value>
  </property>
</configuration>
''')

# hdfs-site.xml for cluster_a (HA nameservice_a)
write_file(f'{base}/cluster_a/conf/hdfs-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>dfs.nameservices</name>
    <value>nameservice_a</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.nameservice_a</name>
    <value>nn1</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.nameservice_a.nn1</name>
    <value>192.168.0.211:8020</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.nameservice_a.nn1</name>
    <value>192.168.0.211:9870</value>
  </property>
  <property>
    <name>dfs.client.failover.proxy.provider.nameservice_a</name>
    <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
  </property>
</configuration>
''')

# hive-site.xml for cluster_a (Kerberos HMS on port 9084, MySQL hive_a)
write_file(f'{base}/cluster_a/conf/hive-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://192.168.0.211:3306/hive_a?createDatabaseIfNotExist=true&amp;useSSL=false</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.jdbc.Driver</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>root</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>thinker</value>
  </property>
  <property>
    <name>hive.metastore.schema.verification</name>
    <value>false</value>
  </property>
  <property>
    <name>hive.metastore.event.db.notification.api.auth</name>
    <value>false</value>
  </property>
  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>/user/hive_a/warehouse</value>
  </property>
  <property>
    <name>hive.metastore.uris</name>
    <value>thrift://192.168.0.211:9084</value>
  </property>
  <property>
    <name>hive.metastore.sasl.enabled</name>
    <value>true</value>
  </property>
  <property>
    <name>hive.metastore.kerberos.keytab.file</name>
    <value>/data/deploy/keytabs/hive.service.keytab</value>
  </property>
  <property>
    <name>hive.metastore.kerberos.principal</name>
    <value>hive/cluster_a@SR.TEST</value>
  </property>
</configuration>
''')

# ====== Cluster B ======

# core-site.xml for cluster_b
write_file(f'{base}/cluster_b/conf/core-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://nameservice_b</value>
  </property>
  <property>
    <name>hadoop.security.authentication</name>
    <value>kerberos</value>
  </property>
  <property>
    <name>hadoop.security.authorization</name>
    <value>true</value>
  </property>
</configuration>
''')

# hdfs-site.xml for cluster_b (HA nameservice_b)
write_file(f'{base}/cluster_b/conf/hdfs-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>dfs.nameservices</name>
    <value>nameservice_b</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.nameservice_b</name>
    <value>nn1</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.nameservice_b.nn1</name>
    <value>192.168.0.211:8020</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.nameservice_b.nn1</name>
    <value>192.168.0.211:9870</value>
  </property>
  <property>
    <name>dfs.client.failover.proxy.provider.nameservice_b</name>
    <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
  </property>
</configuration>
''')

# hive-site.xml for cluster_b (Kerberos HMS on port 9085, MySQL hive_b)
write_file(f'{base}/cluster_b/conf/hive-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://192.168.0.211:3306/hive_b?createDatabaseIfNotExist=true&amp;useSSL=false</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.jdbc.Driver</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>root</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>thinker</value>
  </property>
  <property>
    <name>hive.metastore.schema.verification</name>
    <value>false</value>
  </property>
  <property>
    <name>hive.metastore.event.db.notification.api.auth</name>
    <value>false</value>
  </property>
  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>/user/hive_b/warehouse</value>
  </property>
  <property>
    <name>hive.metastore.uris</name>
    <value>thrift://192.168.0.211:9085</value>
  </property>
  <property>
    <name>hive.metastore.sasl.enabled</name>
    <value>true</value>
  </property>
  <property>
    <name>hive.metastore.kerberos.keytab.file</name>
    <value>/data/deploy/keytabs/hive.service.keytab</value>
  </property>
  <property>
    <name>hive.metastore.kerberos.principal</name>
    <value>hive/cluster_b@SR.TEST</value>
  </property>
</configuration>
''')

print('All config files written')

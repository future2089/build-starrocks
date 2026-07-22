import os

base = '/data/starrocks-deploy'

def write_file(path, content):
    with open(path, 'w', newline='\n') as f:
        f.write(content)

# Cluster A core-site.xml
write_file(f'{base}/cluster_a/conf/core-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://192.168.0.211:8020</value>
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
    <name>dfs.nameservices</name>
    <value>nameservice_a</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.nameservice_a</name>
    <value>nn1,nn2</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.nameservice_a.nn1</name>
    <value>192.168.0.211:8020</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.nameservice_a.nn2</name>
    <value>192.168.0.211:8020</value>
  </property>
  <property>
    <name>dfs.client.failover.proxy.provider.nameservice_a</name>
    <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
  </property>
</configuration>
''')

# Cluster B core-site.xml
write_file(f'{base}/cluster_b/conf/core-site.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://192.168.0.211:8020</value>
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
    <name>dfs.nameservices</name>
    <value>nameservice_b</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.nameservice_b</name>
    <value>nn1,nn2</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.nameservice_b.nn1</name>
    <value>192.168.0.211:8020</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.nameservice_b.nn2</name>
    <value>192.168.0.211:8020</value>
  </property>
  <property>
    <name>dfs.client.failover.proxy.provider.nameservice_b</name>
    <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
  </property>
</configuration>
''')

print('Done')

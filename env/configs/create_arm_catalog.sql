CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.client.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab",
    "hadoop.security.authentication" = "kerberos",
    "hadoop.security.authorization" = "true",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider",
    "aws.s3.use_instance_profile" = "false",
    "aws.s3.region" = "us-east-1"
);

import subprocess

sqls = [
    'DROP CATALOG IF EXISTS hive_arm;',
    '''CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.client.kerberos.principal" = "starrocks/arm-query@ARM.SR.TEST",
    "hive.metastore.kerberos.principal" = "starrocks/arm-query@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab",
    "hadoop.security.authentication" = "kerberos",
    "hadoop.security.authorization" = "true",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider",
    "aws.s3.use_instance_profile" = "false",
    "aws.s3.region" = "us-east-1"
);''',
    'SHOW CATALOGS;',
]

for sql in sqls:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', sql],
        capture_output=True
    )
    if r.returncode != 0 and 'already exists' not in r.stderr.decode():
        print('ERROR running:', sql[:60])
        print('STDERR:', r.stderr.decode()[:300])
    else:
        out = r.stdout.decode().strip()
        if out:
            print(out)

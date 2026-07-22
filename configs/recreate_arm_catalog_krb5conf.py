import subprocess

# Drop and recreate hive_arm catalog with per-catalog krb5.conf
commands = """
DROP CATALOG IF EXISTS hive_arm;
CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.client.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab",
    "hive.metastore.kerberos.krb5.conf" = "/opt/starrocks/fe/meta/krb5_arm.conf",
    "hadoop.security.authentication" = "kerberos",
    "hadoop.security.authorization" = "true",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider"
);
"""

# Run DROP + CREATE
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e',
     commands],
    capture_output=True, text=True, timeout=15
)
print("=== DROP + CREATE ===")
print(r.stdout.strip()[:500] if r.stdout else '(empty)')
print(r.stderr.strip()[:500] if r.stderr else '(no error)')

# Verify
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print("\n=== SHOW DATABASES FROM hive_arm ===")
print(r2.stdout.strip() if r2.stdout else '(empty)')
print(r2.stderr.strip()[:500] if r2.stderr else '')

# Show catalogs
r3 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e',
     'SHOW CATALOGS;'],
    capture_output=True, text=True, timeout=15
)
print("\n=== SHOW CATALOGS ===")
print(r3.stdout.strip()[:500] if r3.stdout else '(empty)')
print(r3.stderr.strip()[:500] if r3.stderr else '')

import subprocess

# First, let's also remove the per-catalog krb5.conf to simplify and just test the fix
# Since the fix now reads client.kerberos.principal, let me update the catalog
# to use starrocks-arm.keytab (which has starrocks/arm-query) and set the client principal
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e',
     'DROP CATALOG IF EXISTS hive_arm;'],
    capture_output=True, text=True, timeout=15
)

# Create with client principal pointing to starrocks-arm.keytab
# This tests the fix: client.kerberos.principal = starrocks/arm-query@ARM.SR.TEST
# with keytab starrocks-arm.keytab (which has that principal)
create_sql = """
CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.client.kerberos.principal" = "starrocks/arm-query@ARM.SR.TEST",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab",
    "hadoop.security.authentication" = "kerberos",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider"
);
"""
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e', create_sql],
    capture_output=True, text=True, timeout=15
)
print("=== CREATE ===")
print(r2.stderr.strip() if r2.stderr else '(no error)')

# Verify
r3 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print("\n=== SHOW DATABASES FROM hive_arm ===")
print(r3.stdout.strip() if r3.stdout else '(empty)')
print(r3.stderr.strip()[:500] if r3.stderr else '')

import subprocess

# First test: without krb5.conf, just fix keytab
commands = """
DROP CATALOG IF EXISTS hive_arm;
CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab",
    "hadoop.security.authentication" = "kerberos",
    "hadoop.security.authorization" = "true",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider"
);
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e', commands],
    capture_output=True, text=True, timeout=15
)
print("=== DROP + CREATE (no krb5.conf) ===")
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

# Now add krb5.conf via ALTER
if r2.stdout.strip():
    r3 = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e',
         'ALTER CATALOG hive_arm SET ("hive.metastore.kerberos.krb5.conf" = "/opt/starrocks/fe/meta/krb5_arm.conf");'],
        capture_output=True, text=True, timeout=15
    )
    print("\n=== ALTER add krb5.conf ===")
    print(r3.stdout.strip()[:500] if r3.stdout else '(empty)')
    print(r3.stderr.strip()[:500] if r3.stderr else '(no error)')
    
    # Re-verify
    r4 = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
         'SHOW DATABASES FROM hive_arm;'],
        capture_output=True, text=True, timeout=30
    )
    print("\n=== SHOW DATABASES FROM hive_arm (after krb5.conf added) ===")
    print(r4.stdout.strip() if r4.stdout else '(empty)')
    print(r4.stderr.strip()[:500] if r4.stderr else '')

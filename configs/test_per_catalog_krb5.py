import subprocess

# Test WITH per-catalog krb5.conf
commands_krb5 = """
DROP CATALOG IF EXISTS hive_arm;
CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab",
    "hive.metastore.kerberos.krb5.conf" = "/opt/starrocks/fe/meta/krb5_arm.conf",
    "hadoop.security.authentication" = "kerberos",
    "hadoop.security.authorization" = "true",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider"
);
"""

r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e', commands_krb5],
    capture_output=True, text=True, timeout=15
)
print("=== DROP + CREATE (with krb5.conf) ===")
print(r.stdout.strip()[:500] if r.stdout else '(empty)')
print(r.stderr.strip()[:500] if r.stderr else '(no error)')

# Verify
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print("\n=== SHOW DATABASES FROM hive_arm (with per-catalog krb5.conf) ===")
print(r2.stdout.strip() if r2.stdout else '(empty)')
print(r2.stderr.strip()[:500] if r2.stderr else '')

# Show the catalog's properties for verification
r3 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW CREATE CATALOG hive_arm;'],
    capture_output=True, text=True, timeout=15
)
print("\n=== Catalog properties ===")
prop = r3.stdout.strip().replace('\\n', '\n')
# Show only krb5-related properties
for line in prop.split('\n'):
    if 'krb5' in line.lower() or 'kerberos' in line.lower() or 'keytab' in line.lower():
        print(line.strip())

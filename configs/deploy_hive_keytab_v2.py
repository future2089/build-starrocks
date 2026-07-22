import subprocess, base64, os

# Get ALL base64 output (skip the "Authorized users" banner)
r = subprocess.run("ssh -o LogLevel=QUIET root@192.168.0.181 base64 /tmp/hive-arm.keytab",
    shell=True, capture_output=True, text=True, timeout=15)

lines = r.stdout.strip().split('\n')
b64 = ''.join([l.strip() for l in lines if l.strip() and not l.startswith('Authorized')])
print('B64 length:', len(b64))

data = base64.b64decode(b64)
print('Size:', len(data), 'bytes')

with open('/tmp/hive-arm.keytab', 'wb') as f:
    f.write(data)

try:
    r = subprocess.run(['klist', '-ket', '/tmp/hive-arm.keytab'], capture_output=True, text=True)
    print(r.stdout)
except FileNotFoundError:
    print('klist not available (expected)')

subprocess.run(['docker', 'cp', '/tmp/hive-arm.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/hive-arm.keytab'], check=True)
print('DEPLOYED')

# Now update the catalog
sqls = [
    'DROP CATALOG IF EXISTS hive_arm;',
    '''CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.client.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab",
    "hadoop.security.authentication" = "kerberos",
    "hadoop.security.authorization" = "true",
    "dfs.nameservices" = "arm-ha",
    "dfs.ha.namenodes.arm-ha" = "nn1",
    "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8020",
    "dfs.client.failover.proxy.provider.arm-ha" = "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider",
    "aws.s3.use_instance_profile" = "false",
    "aws.s3.region" = "us-east-1"
);''',
    'SHOW DATABASES FROM hive_arm;',
]

for sql in sqls:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', sql],
        capture_output=True, text=True, timeout=30
    )
    out = r.stdout.strip()
    err = r.stderr.strip()
    if out:
        print(f'OK: {out[:120]}')
    elif err:
        print(f'ERR: {err[:200]}')
    else:
        print('OK (no output)')

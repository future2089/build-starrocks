import subprocess

sqls = [
    'DROP CATALOG IF EXISTS hive_arm;',
    '''CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab"
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
        print(f'OUT: {out}')
    elif err:
        print(f'ERR: {err[:300]}')
    else:
        print('OK')

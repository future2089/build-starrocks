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
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab",
    "hadoop.security.auth_to_local" = "RULE:[1:$1](hive/.*@ARM.SR.TEST)s/.*/hive/\\nRULE:[2:$1@$0](.*)s/.*/hive/\\nDEFAULT"
);''',
    'SHOW DATABASES FROM hive_arm;',
]

for sql in sqls:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', sql],
        capture_output=True, text=True, timeout=60
    )
    out = r.stdout.strip()
    err = r.stderr.strip()
    if out:
        print(f'OUT: {out[:500]}')
    elif err:
        print(f'ERR: {err[:500]}')
    else:
        print('OK')

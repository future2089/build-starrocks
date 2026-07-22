import subprocess

sqls = [
    'DROP CATALOG IF EXISTS hive_arm;',
    '''CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083"
);''',
    'SHOW CREATE CATALOG hive_arm;',
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
        print(f'OUT: {out[:200]}...' if len(out) > 200 else f'OUT: {out}')
        print()
    elif err:
        print(f'ERR: {err[:200]}')
    else:
        print('OK')

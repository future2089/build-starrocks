import subprocess
import time

# Wait for FE to be ready
print("Waiting for FE to start...")
for i in range(30):
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SELECT 1'],
        capture_output=True, text=True, timeout=10
    )
    if r.stdout.strip() == '1':
        print(f'FE ready after {i*2}s')
        break
    time.sleep(2)
else:
    print('FE not ready')
    exit(1)

# Drop catalog
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'DROP CATALOG IF EXISTS hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print('drop:', r.stderr.strip()[:200] if r.stderr else 'OK')

# Create catalog
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     '''CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://192.168.0.181:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab"
);'''],
    capture_output=True, text=True, timeout=30
)
print('create:', r.stderr.strip()[:200] if r.stderr else 'OK')

# Test
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
out = r.stdout.strip()
err = r.stderr.strip()
if out:
    print(f'SUCCESS: {out[:500]}')
elif err:
    print(f'FAIL: {err[:500]}')
else:
    print('NO OUTPUT')

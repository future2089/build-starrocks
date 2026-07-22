import subprocess
import time

# Restart FE
r = subprocess.run(
    'docker exec sr-deploy bash -c "cd /opt/starrocks && nohup ./fe/bin/start_fe.sh > /dev/null 2>&1 &"',
    shell=True, capture_output=True, text=True, timeout=15
)
print('Restart sent, waiting...')
time.sleep(10)

# Check FE process
r = subprocess.run(
    'docker exec sr-deploy bash -c "ps aux | grep -c FeServer"',
    shell=True, capture_output=True, text=True, timeout=10
)
fe_count = r.stdout.strip()
print(f'FE processes: {fe_count}')

# Wait for FE to be ready
for i in range(30):
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SELECT 1'],
        capture_output=True, text=True, timeout=10
    )
    if r.stdout.strip() == '1':
        print(f'FE ready after {i+1}s')
        break
    time.sleep(2)
else:
    print('FE not ready')

# Drop and recreate catalog
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'DROP CATALOG IF EXISTS hive_arm;'],
    capture_output=True, text=True, timeout=10
)
print('drop:', r.stderr.strip()[:200] if r.stderr else 'OK')

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
    capture_output=True, text=True, timeout=10
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

# Show last 10 log lines for arm-hive
r = subprocess.run(
    "docker exec sr-deploy grep 'arm-hive' /opt/starrocks/fe/log/fe.out | tail -20",
    shell=True, capture_output=True, text=True, timeout=10
)
print(f'Log tail:\n{r.stdout.strip()[:1000]}')

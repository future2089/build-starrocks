import subprocess

# Step 1: Add arm-hive to /etc/hosts in sr-deploy container
r = subprocess.run(
    'docker exec sr-deploy bash -c \'grep -q "arm-hive" /etc/hosts; if [ $? -ne 0 ]; then echo "192.168.0.181 arm-hive" >> /etc/hosts; fi\'',
    shell=True, capture_output=True, text=True, timeout=15
)
print('hosts:', r.stdout.strip(), r.stderr.strip()[:200] if r.stderr else '')

# Step 2: Drop and recreate hive_arm with hostname instead of IP
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'DROP CATALOG IF EXISTS hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print('drop:', r.stdout.strip(), r.stderr.strip()[:200] if r.stderr else '')

r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     '''CREATE EXTERNAL CATALOG hive_arm
PROPERTIES
(
    "type" = "hive",
    "hive.metastore.uris" = "thrift://arm-hive:9083",
    "hive.metastore.sasl.enabled" = "true",
    "hive.metastore.kerberos.principal" = "hive/arm-hive@ARM.SR.TEST",
    "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab"
);'''],
    capture_output=True, text=True, timeout=30
)
print('create:', r.stdout.strip(), r.stderr.strip()[:200] if r.stderr else 'OK')

# Step 3: Test
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
out = r.stdout.strip()
err = r.stderr.strip()
if out:
    print('SUCCESS:', out[:500])
elif err:
    print('FAIL:', err[:500])
else:
    print('NO OUTPUT')

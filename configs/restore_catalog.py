import subprocess

# First check the file on FE
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'cat', '/opt/starrocks/fe/meta/krb5_arm.conf'],
    capture_output=True, text=True, timeout=10
)
print("=== krb5_arm.conf on FE ===")
print(r.stdout.strip())
print(r.stderr.strip()[:500] if r.stderr else '')

# Try ALTER to remove the krb5.conf property
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e',
     'ALTER CATALOG hive_arm SET ("hive.metastore.kerberos.krb5.conf" = "");'],
    capture_output=True, text=True, timeout=15
)
print("\n=== ALTER remove krb5.conf ===")
print(r2.stdout.strip()[:500] if r2.stdout else '(empty)')
print(r2.stderr.strip()[:500] if r2.stderr else '(no error)')

# Verify catalog works again
r3 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=15
)
print("\n=== SHOW DATABASES FROM hive_arm (after restore) ===")
print(r3.stdout.strip() if r3.stdout else '(empty)')
print(r3.stderr.strip()[:500] if r3.stderr else '')

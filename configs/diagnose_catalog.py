import subprocess

# Get the full properties of the hive_arm catalog
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW CREATE CATALOG hive_arm;'],
    capture_output=True, text=True, timeout=15
)
print("=== SHOW CREATE CATALOG hive_arm ===")
for line in r.stdout.split('\n'):
    print(line[:200])

print("\n=== STDERR ===")
print(r.stderr.strip()[:500] if r.stderr else '(no error)')

# Also check if starrocks-arm.keytab actually has hive/arm-hive
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'klist', '-k', '/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'],
    capture_output=True, text=True, timeout=10
)
print("\n=== starrocks-arm.keytab ===")
print(r2.stdout.strip())
print(r2.stderr.strip()[:500] if r2.stderr else '')

r3 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'klist', '-k', '/opt/starrocks/fe/meta/keytabs/hive-arm.keytab'],
    capture_output=True, text=True, timeout=10
)
print("\n=== hive-arm.keytab ===")
print(r3.stdout.strip())
print(r3.stderr.strip()[:500] if r3.stderr else '')

import subprocess

# Try ALTER CATALOG first
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e',
     "ALTER CATALOG hive_arm SET (\"hive.metastore.kerberos.krb5.conf\" = \"/opt/starrocks/fe/meta/krb5_arm.conf\");"],
    capture_output=True, text=True, timeout=15
)

print("ALTER CATALOG result:")
print(r.stdout.strip()[:500] if r.stdout else '(empty)')
print(r.stderr.strip()[:500] if r.stderr else '(no error)')

# Check current catalog properties
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     "SELECT * FROM information_schema.catalogs WHERE catalog_name = 'hive_arm';"],
    capture_output=True, text=True, timeout=15
)
print("\nCurrent catalog properties:")
print(r2.stdout.strip()[:1000] if r2.stdout else '(empty)')

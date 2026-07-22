import subprocess

# Verify the FE is running and all catalogs work
for catalog in ['hive_arm', 'hive_a', 'hive_b']:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
         f'SHOW DATABASES FROM {catalog};'],
        capture_output=True, text=True, timeout=30
    )
    print(f"=== {catalog} ===")
    out = r.stdout.strip()
    if out:
        for line in out.split('\n'):
            print(f"  {line}")
    else:
        print(f"  (empty/error)")
    err = r.stderr.strip()
    if err:
        print(f"  ERROR: {err[:300]}")

# Also verify the new class is loaded
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW CATALOGS;'],
    capture_output=True, text=True, timeout=15
)
print("\n=== Catalogs ===")
for line in r2.stdout.strip().split('\n'):
    print(f"  {line}")

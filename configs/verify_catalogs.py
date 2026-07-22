import subprocess

# Verify hive_arm still works
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=15
)
print("=== SHOW DATABASES FROM hive_arm ===")
print(r.stdout.strip() if r.stdout else '(empty)')
print(r.stderr.strip()[:500] if r.stderr else '')

# Also verify hive_a and hive_b still work
for c in ['hive_a', 'hive_b']:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
         f'SHOW DATABASES FROM {c};'],
        capture_output=True, text=True, timeout=15
    )
    print(f"\n=== SHOW DATABASES FROM {c} ===")
    print(r.stdout.strip() if r.stdout else '(empty)')
    print(r.stderr.strip()[:500] if r.stderr else '')

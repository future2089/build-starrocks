import subprocess

# Verify hive_arm catalog
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print("=== SHOW DATABASES FROM hive_arm ===")
print(r.stdout.strip() if r.stdout else '(empty)')
print(r.stderr.strip()[:500] if r.stderr else '')

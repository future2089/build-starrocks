import subprocess

# Test hive_arm catalog
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print('hive_arm result:')
print('STDOUT:', r.stdout.strip())
print('STDERR:', r.stderr.strip()[:500])

# Also test hive_a
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SHOW DATABASES FROM hive_a;'],
    capture_output=True, text=True, timeout=30
)
print('\nhive_a result:')
print('STDOUT:', r.stdout.strip())
print('STDERR:', r.stderr.strip()[:500])

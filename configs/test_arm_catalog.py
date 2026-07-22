import subprocess

r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'USE hive_arm.`default`; SHOW TABLES;'],
    capture_output=True, text=True, timeout=30
)
print('STDOUT:', r.stdout.strip())
print('STDERR:', r.stderr.strip()[:500])

# Also try listing databases from hive_arm
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
print('\nDatabases:')
print(r2.stdout.strip())
print(r2.stderr.strip()[:500] if r2.stderr else '')

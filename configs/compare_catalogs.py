import subprocess

for catalog in ['hive_a', 'hive_b', 'hive_arm']:
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', f'SHOW CREATE CATALOG {catalog};'],
        capture_output=True, text=True, timeout=30
    )
    print(f'\n=== {catalog} ===')
    print(r.stdout.strip())

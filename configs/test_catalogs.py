import subprocess
catalogs = ['hive_a', 'hive_b', 'hive_arm']
for cat in catalogs:
    r = subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', f'SHOW DATABASES FROM {cat};'], capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        dbs = r.stdout.strip().replace('\n', ', ')
        print(f'{cat}: OK ({dbs})')
    else:
        err = r.stderr[:100].replace('\n', ' ')
        print(f'{cat}: FAIL - {err}')

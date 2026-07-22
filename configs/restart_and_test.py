import subprocess
import time

# Restart FE
print('Restarting FE...')
r = subprocess.run(
    'docker exec sr-deploy bash -c "cd /opt/starrocks && ./fe/bin/start_fe.sh --daemon"',
    shell=True, capture_output=True, text=True, timeout=10
)
print('Restart sent')

# Wait for FE to be ready
print('Waiting for FE...')
for i in range(40):
    r = subprocess.run(
        ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SELECT 1'],
        capture_output=True, text=True, timeout=10
    )
    if r.stdout.strip() == '1':
        print(f'FE ready after {i+1}s')
        break
    time.sleep(2)
else:
    print('FE not ready after 80s')

# Test hive_arm catalog
print('\nTesting hive_arm catalog...')
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SHOW DATABASES FROM hive_arm;'],
    capture_output=True, text=True, timeout=30
)
out = r.stdout.strip()
err = r.stderr.strip()
if out:
    print(f'SUCCESS: {out[:500]}')
elif err:
    print(f'FAIL: {err[:500]}')
else:
    print('NO OUTPUT')

# Also test hive_a (SR.TEST) to make sure it still works
print('\nTesting hive_a catalog (SR.TEST, should still work)...')
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', 'SHOW DATABASES FROM hive_a;'],
    capture_output=True, text=True, timeout=30
)
out = r.stdout.strip()
err = r.stderr.strip()
if out:
    print(f'hive_a OK: {out[:200]}')
elif err:
    print(f'hive_a FAIL: {err[:500]}')

import subprocess

# Check KVNO - run kadmin from 211 to 181
r = subprocess.run(
    ['ssh', 'root@192.168.0.181', 'kadmin.local -q "getprinc hive/arm-hive@ARM.SR.TEST" 2>&1 | head -30'],
    capture_output=True, text=True, timeout=10
)
out = r.stdout.strip()
err = r.stderr.strip()
print('OUT:', out or 'EMPTY')
print('ERR:', err[:500] if err else 'NONE')

# Also check KDC kvno
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.181', 'kadmin.local -q "getstrs hive/arm-hive@ARM.SR.TEST" 2>&1 | head -10 || kadmin.local -q "getprinc hive/arm-hive@ARM.SR.TEST" 2>&1 | grep -i kvno'],
    capture_output=True, text=True, timeout=10
)
out2 = r2.stdout.strip()
err2 = r2.stderr.strip()
print('KVNO:', out2 or 'EMPTY')
if err2:
    print('ERR2:', err2[:500])

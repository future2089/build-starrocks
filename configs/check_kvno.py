import subprocess

# Check KVNO from 181 KDC
r = subprocess.run(
    ['ssh', 'root@192.168.0.181', 'kadmin.local -q "getprinc hive/arm-hive@ARM.SR.TEST" 2>&1 | head -30'],
    capture_output=True, text=True, timeout=15
)
out = r.stdout.strip()
err = r.stderr.strip()
print('181 KDC output:')
print(out if out else 'EMPTY')
if err:
    print('STDERR:', err[:500])

import subprocess, base64

# Get ALL base64 output (skip the "Authorized users" banner)
r = subprocess.run("ssh -o LogLevel=QUIET root@192.168.0.181 base64 /tmp/hive-arm.keytab",
    shell=True, capture_output=True, text=True, timeout=15)

# First line is "Authorized users...", rest is base64
lines = r.stdout.strip().split('\n')
b64 = ''.join([l.strip() for l in lines if l.strip() and not l.startswith('Authorized')])
print('B64 length:', len(b64), 'B64 first 30:', b64[:30])

data = base64.b64decode(b64)
print('Size:', len(data), 'bytes')

with open('/tmp/hive-arm.keytab', 'wb') as f:
    f.write(data)

# Verify
r = subprocess.run(['klist', '-ket', '/tmp/hive-arm.keytab'], capture_output=True, text=True)
if r.returncode != 0:
    # klist not available, just check size
    print('Skipping klist, size:', len(data))
else:
    print(r.stdout)

subprocess.run(['docker', 'cp', '/tmp/hive-arm.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/hive-arm.keytab'], check=True)
print('DEPLOYED')

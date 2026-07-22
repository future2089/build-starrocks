import subprocess

# Get base64 keytab from 181
cmd = "ssh root@192.168.0.181 'base64 /tmp/starrocks-arm.keytab'"
r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
if r.returncode != 0:
    print('ERROR fetching keytab:', r.stderr)
    exit(1)

b64 = r.stdout.strip()
print('B64 length:', len(b64))

# Save to file, then copy to container
with open('/tmp/starrocks-arm.keytab', 'wb') as f:
    import base64
    f.write(base64.b64decode(b64))

# Verify
r = subprocess.run(['klist', '-ket', '/tmp/starrocks-arm.keytab'], capture_output=True, text=True)
print('KLIST OUT:', r.stdout)
print('KLIST ERR:', r.stderr)

# Copy to container
subprocess.run(['docker', 'cp', '/tmp/starrocks-arm.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
print('COPIED')

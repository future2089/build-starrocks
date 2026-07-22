import subprocess, base64

# Get base64 keytab from 181 (clean copy)
r = subprocess.run("ssh root@192.168.0.181 'cat /tmp/starrocks-arm.keytab | base64 -w0'", shell=True, capture_output=True, text=True, timeout=30)
if r.returncode != 0:
    print('ERROR:', r.stderr)
    exit(1)

b64 = r.stdout.strip()
print('Base64 length:', len(b64))

# Decode
data = base64.b64decode(b64)
print('Keytab size:', len(data), 'bytes')

# Write locally on 211
with open('/tmp/starrocks-arm.keytab', 'wb') as f:
    f.write(data)

# Copy into container
subprocess.run(['docker', 'cp', '/tmp/starrocks-arm.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
print('COPIED')

import subprocess, base64

# Get base64 from 181
r = subprocess.run("ssh root@192.168.0.181 'base64 /tmp/starrocks-arm-rc4.keytab'", shell=True, capture_output=True, text=True, timeout=30)
if r.returncode != 0:
    print('ERROR:', r.stderr)
    exit(1)

b64 = r.stdout.strip()
data = base64.b64decode(b64)
print('Keytab size:', len(data))

with open('/tmp/starrocks-arm-rc4.keytab', 'wb') as f:
    f.write(data)

subprocess.run(['docker', 'cp', '/tmp/starrocks-arm-rc4.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
print('DEPLOYED')

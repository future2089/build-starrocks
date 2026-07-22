import subprocess, base64

# Get RC4 keytab from 181
r = subprocess.run("ssh root@192.168.0.181 'base64 /tmp/starrocks-arm-rc4.keytab'", shell=True, capture_output=True, text=True, timeout=30)
b64_lines = [l.strip() for l in r.stdout.strip().split('\n') if l.strip() and not l.strip().startswith('Authorized')]
full_b64 = ''.join(b64_lines)
print('B64 first 40:', full_b64[:40])

data = base64.b64decode(full_b64)
print('Size:', len(data), 'bytes')

with open('/tmp/starrocks-arm-v3.keytab', 'wb') as f:
    f.write(data)

# Copy to container
subprocess.run(['docker', 'cp', '/tmp/starrocks-arm-v3.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)

# Verify using python to parse keytab
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'python3', '-c', 
    'import base64; d=open(\"/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab\",\"rb\").read(); print(\"Size:\",len(d),\"B64:\",base64.b64encode(d[:12]).decode())'],
    capture_output=True, text=True, timeout=10)
print('Container keytab:', r.stdout.strip())
print('DEPLOYED')

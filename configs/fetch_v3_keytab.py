import subprocess, base64

# Get current correct keytab from 181 KDC with vno 3
cmd = "ssh root@192.168.0.181 'echo ktadd -k /tmp/starrocks-arm-v3.keytab -e arcfour-hmac:normal starrocks/arm-query@ARM.SR.TEST | kadmin.local && base64 /tmp/starrocks-arm-v3.keytab'"
r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

# Extract base64 from output (everything after kadmin.local: prompt)
lines = r.stdout.strip().split('\n')
b64_lines = [l for l in lines if l and not l.startswith('Authenticating') and not l.startswith('kadmin') and not l.startswith('Entry') and not l.startswith('    ')]
b64 = ''.join(b64_lines)
b64 = b64.replace(' ', '').replace('\n', '').replace('\r', '')
print('B64:', b64[:50])

data = base64.b64decode(b64)
print('Size:', len(data), 'bytes')

with open('/tmp/starrocks-arm-v3.keytab', 'wb') as f:
    f.write(data)

# Verify with klist if available
r = subprocess.run(['klist', '-ket', '/tmp/starrocks-arm-v3.keytab'], capture_output=True, text=True)
print('KLIST:', r.stdout)

# Copy to container
subprocess.run(['docker', 'cp', '/tmp/starrocks-arm-v3.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
print('DEPLOYED')

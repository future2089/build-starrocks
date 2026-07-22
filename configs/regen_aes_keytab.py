import subprocess, base64

# Remove and recreate principal with proper AES keys
cmds = [
    "ssh root@192.168.0.181 'echo -e \"delete_principal starrocks/arm-query@ARM.SR.TEST\\naddprinc -randkey starrocks/arm-query@ARM.SR.TEST\\nktadd -k /tmp/starrocks-arm-aes.keytab starrocks/arm-query@ARM.SR.TEST\\n\" | kadmin.local 2>&1'",
    "ssh root@192.168.0.181 'klist -ket /tmp/starrocks-arm-aes.keytab'",
]

for cmd in cmds:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    print(f'=== {cmd[:60]} ===')
    print(r.stdout)

# Get base64
r = subprocess.run("ssh root@192.168.0.181 'base64 /tmp/starrocks-arm-aes.keytab'", shell=True, capture_output=True, text=True, timeout=30)
b64 = r.stdout.strip().split('\n')[-1]  # last non-empty line
data = base64.b64decode(b64)
print('KEYTAB size:', len(data), 'bytes')

with open('/tmp/starrocks-arm-aes.keytab', 'wb') as f:
    f.write(data)

subprocess.run(['docker', 'cp', '/tmp/starrocks-arm-aes.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
print('DEPLOYED')

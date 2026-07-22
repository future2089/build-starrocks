import subprocess, base64

# Create keytab for hive/arm-hive on ARM KDC
cmds = "ktadd -k /tmp/hive-arm.keytab hive/arm-hive@ARM.SR.TEST"
r = subprocess.run(['ssh', 'root@192.168.0.181', 'echo "{}" | kadmin.local'.format(cmds)],
    capture_output=True, text=True, timeout=30)
print('KTADD:', r.stdout)

# Verify
r = subprocess.run("ssh root@192.168.0.181 'klist -ket /tmp/hive-arm.keytab'",
    shell=True, capture_output=True, text=True, timeout=15)
print('KLIST:', r.stdout)

# Get base64
r = subprocess.run("ssh root@192.168.0.181 'base64 /tmp/hive-arm.keytab'",
    shell=True, capture_output=True, text=True, timeout=15)
b64 = r.stdout.strip().split('\n')[-1]
data = base64.b64decode(b64)
print('Size:', len(data), 'bytes')

with open('/tmp/hive-arm.keytab', 'wb') as f:
    f.write(data)

subprocess.run(['docker', 'cp', '/tmp/hive-arm.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/hive-arm.keytab'], check=True)
print('DEPLOYED')

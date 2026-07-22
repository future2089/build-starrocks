import subprocess

# First try to install krb5-user with non-interactive mode
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'bash', '-c', 
    'DEBIAN_FRONTEND=noninteractive apt-get install -y krb5-user 2>&1 | tail -5'],
    capture_output=True, text=True, timeout=120)
print('INSTALL:', r.returncode)
print(r.stdout)
print(r.stderr[-200:])

# Try kinit
r = subprocess.run(['docker', 'exec', 'sr-deploy',
    'kinit', '-V', '-kt', '/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab',
    'starrocks/arm-query@ARM.SR.TEST'],
    capture_output=True, text=True, timeout=15)
print('KINIT RC:', r.returncode)
print('STDOUT:', r.stdout)
print('STDERR:', r.stderr)

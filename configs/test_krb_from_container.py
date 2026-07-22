import subprocess, os

# Install krb5-user for debug
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'apt-get', 'update'], capture_output=True, text=True, timeout=120)
print('apt update:', r.returncode)

r = subprocess.run(['docker', 'exec', 'sr-deploy', 'apt-get', 'install', '-y', 'krb5-user'], capture_output=True, text=True, timeout=120)
print('install krb5-user:', r.returncode)
if r.returncode != 0:
    print(r.stderr[-300:])

# Try kinit with the keytab using the FE's krb5.conf
r = subprocess.run([
    'docker', 'exec', '-e', 'KRB5_CONFIG=/opt/starrocks/fe/meta/krb5.conf',
    'sr-deploy',
    'kinit', '-V', '-kt', '/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab', 'starrocks/arm-query@ARM.SR.TEST'
], capture_output=True, text=True, timeout=30)
print('KINIT RC:', r.returncode)
print('STDOUT:', r.stdout)
print('STDERR:', r.stderr)

import subprocess, base64

# First try without delete, just addprinc (should fail if exists, then we delete and redo)
# Approach: use the original vno 2 keytab which had AES256 - it should still work!
# Actually the KDC changed the key when we did ktadd -e arcfour-hmac
# We need to re-add the principal with AES

# Use a here-doc style for kadmin
cmds = """
addprinc -randkey starrocks/arm-query@ARM.SR.TEST
ktadd -k /tmp/starrocks-arm-aes-v2.keytab starrocks/arm-query@ARM.SR.TEST
"""
r = subprocess.run(['ssh', 'root@192.168.0.181', 'echo "{}" | kadmin.local'.format(cmds.strip())], 
    capture_output=True, text=True, timeout=30)
print('STDOUT:', r.stdout)
print('STDERR:', r.stderr[:200])

# Get keytab
r = subprocess.run("ssh root@192.168.0.181 'base64 /tmp/starrocks-arm-aes-v2.keytab'", shell=True, capture_output=True, text=True, timeout=15)
b64 = r.stdout.strip()
# Remove any non-base64 lines
lines = [l.strip() for l in b64.split('\n') if l.strip() and not l.startswith('Authorized')]
b64_clean = ''.join(lines)
print('B64 len:', len(b64_clean))
try:
    data = base64.b64decode(b64_clean)
    print('Size:', len(data))
    with open('/tmp/starrocks-arm-aes-v2.keytab', 'wb') as f:
        f.write(data)
    subprocess.run(['docker', 'cp', '/tmp/starrocks-arm-aes-v2.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
    print('DEPLOYED')
except Exception as e:
    print('ERROR:', e)

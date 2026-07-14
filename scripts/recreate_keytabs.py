import subprocess, os

def kadmin(cmd):
    r = subprocess.run(['kadmin.local', '-q', cmd], capture_output=True, text=True)
    print(f'{cmd}: {r.stdout.strip()[:300]}')

# Recreate cluster_a keytab with current keys (no randomize)
kt_a = '/data/starrocks-deploy/cluster_a/keytabs/hive.service.keytab'
kt_b = '/data/starrocks-deploy/cluster_b/keytabs/hive.service.keytab'

# Delete old keytabs
for f in [kt_a, kt_b]:
    if os.path.exists(f):
        os.remove(f)
        print(f'Removed {f}')

# Export cluster_a keytab
kadmin(f'ktadd -norandkey -k {kt_a} hive/localhost@SR.TEST')
kadmin(f'ktadd -norandkey -k {kt_a} hive/cluster_a@SR.TEST')

# Export cluster_b keytab
kadmin(f'ktadd -norandkey -k {kt_b} hive/localhost@SR.TEST')
kadmin(f'ktadd -norandkey -k {kt_b} hive/cluster_b@SR.TEST')

# Verify
for f in [kt_a, kt_b]:
    size = os.path.getsize(f)
    r = subprocess.run(['klist', '-kte', f], capture_output=True, text=True)
    print(f'\n{f} ({size} bytes):')
    for line in r.stdout.strip().split('\n'):
        if 'SR.TEST' in line:
            print(f'  {line.strip()}')

print('\nDONE')

import subprocess, json

# Find which container has /etc/krb5.conf or /var/kerberos/krb5kdc
out = subprocess.run(['docker', 'ps', '-q', '--no-trunc'], capture_output=True, text=True)
for cid in out.stdout.strip().split():
    try:
        r = subprocess.run(['docker', 'exec', cid, 'sh', '-c', 'test -f /etc/krb5.conf && echo YES || echo NO'], capture_output=True, text=True, timeout=5)
        has_krb5 = r.stdout.strip()
        r2 = subprocess.run(['docker', 'exec', cid, 'sh', '-c', 'which krb5kdc 2>/dev/null || echo NOKDC'], capture_output=True, text=True, timeout=5)
        has_kdc = r2.stdout.strip()
        r3 = subprocess.run(['docker', 'inspect', cid, '--format={{.Name}}'], capture_output=True, text=True, timeout=5)
        name = r3.stdout.strip().lstrip('/')
        if has_krb5 == 'YES' or has_kdc != 'NOKDC':
            print(f'{name:20} krb5.conf={has_krb5} krb5kdc={has_kdc}')
    except:
        pass
print('ALL DONE')

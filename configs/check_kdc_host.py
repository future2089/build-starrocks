import subprocess
script = r"""echo "=== KDC process on host ==="
ps aux | grep -i "krb5\|kdc\|kadmind" | grep -v grep | head -10
echo "=== krb5.keytab ==="
ls -la /etc/krb5.keytab 2>/dev/null || echo "no /etc/krb5.keytab"
echo "=== Check kadmin on host ==="
which kadmin.local 2>/dev/null || which kadmin 2>/dev/null || echo "NO kadmin"
echo "=== KDC config ==="
cat /var/kerberos/krb5kdc/kdc.conf 2>/dev/null || cat /etc/krb5kdc/kdc.conf 2>/dev/null || echo "NO kdc.conf"
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_kdc_host.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_kdc_host.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

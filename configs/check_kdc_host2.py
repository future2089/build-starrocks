import subprocess
script = r"""echo "=== Port 88 on host ==="
ss -tlnp 2>/dev/null | grep ":88 "
echo "=== Check host krb5kdc status ==="
ps aux | grep "[k]rb5kdc\|[k]dc" | head -5
echo "=== Check KDC logs ==="
ls /var/log/krb5* 2>/dev/null | head -5
tail -10 /var/log/krb5kdc.log 2>/dev/null | head -20
echo "=== Search for KDC binary ==="
which krb5kdc 2>/dev/null || find / -name krb5kdc -type f 2>/dev/null | head -3
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_kdc_host2.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_kdc_host2.sh'], capture_output=True, text=True, timeout=30)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

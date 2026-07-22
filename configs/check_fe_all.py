import subprocess

script = r"""echo "=== FE process ==="
ps aux | grep -i starrocks | grep -v grep | head -5
echo "=== FE meta dir ==="
ls -la /opt/starrocks/fe/meta/ 2>/dev/null | head -10
echo "=== FE conf ==="
ls -la /opt/starrocks/fe/conf/ 2>/dev/null
echo "=== FE log dir ==="
ls -la /opt/starrocks/fe/log/ 2>/dev/null | head -10
echo "=== Check all krb5.conf ==="
find /opt/starrocks -name "krb5*" 2>/dev/null
echo "=== Check all keytab ==="
find /opt/starrocks -name "*.keytab" 2>/dev/null
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_fe_all.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'bash < /tmp/check_fe_all.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

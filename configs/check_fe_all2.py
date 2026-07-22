import subprocess

script = r"""FE=/data/starrocks-build/starrocks-3.3.17/output/fe
echo "=== FE meta ==="
ls -la $FE/meta/ 2>/dev/null
echo "=== FE conf ==="
ls -la $FE/conf/ 2>/dev/null
grep -i "arm\|keytab\|kerberos\|krb5\|catalog" $FE/conf/fe.conf 2>/dev/null | head -10
echo "=== FE log recent ==="
ls -lt $FE/log/ 2>/dev/null | head -5
echo "=== FE running? ==="
ps aux | grep -i "[s]tarrocks" | grep -v "build\|supervisor\|broker\|director\|feproxy" | grep -v grep | head -5
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'bash < /tmp/check_fe_all2.sh'],
    capture_output=True, text=True, timeout=10
)
# Write the script
subprocess.run(['ssh', 'root@192.168.0.211', 'cat > /tmp/check_fe_all2.sh'], input=script, text=True, timeout=10)
# Run it
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'bash /tmp/check_fe_all2.sh'],
    capture_output=True, text=True, timeout=10
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

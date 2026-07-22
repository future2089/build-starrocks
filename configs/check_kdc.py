import subprocess
script = r"""echo "=== Check KDC on 181 ==="
ss -tlnp 2>/dev/null | grep ":88 " || netstat -tlnp 2>/dev/null | grep ":88 " || echo "NO KDC PORT 88"
echo "=== KDC processes ==="
ps aux | grep -i "krb5kdc\|kadmind\|kdc" | grep -v grep | head -5
echo "=== Test KDC port 88 from inside host 181 ==="
timeout 3 bash -c 'echo "" > /dev/tcp/192.168.0.181/88' 2>&1 && echo "KDC 88 OK" || echo "KDC 88 FAIL"
echo "=== Check kadmin ==="
which kadmin.local 2>/dev/null || echo "no kadmin.local"
ls /usr/sbin/kadmin* 2>/dev/null || echo "no kadmin in /usr/sbin"
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_kdc.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_kdc.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:1500] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

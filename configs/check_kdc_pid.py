import subprocess
script = r"""echo "=== Check KDC PID 3279538 ==="
docker exec hadoop-arm bash -c 'ls /proc/3279538/ 2>/dev/null && cat /proc/3279538/status 2>/dev/null | head -5 || echo "PID NOT FOUND"'
echo "=== Alternative: check all kdc processes ==="
docker exec hadoop-arm bash -c 'ps aux 2>/dev/null | head -100' | grep -i "kdc\|krb5\|kadmin\|krb" | head -5
echo "=== Check /proc/*/status for krb5 ==="
docker exec hadoop-arm bash -c 'grep -l "krb5kdc" /proc/*/status 2>/dev/null' | head -5 || echo "NO KDC FOUND"
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_kdc_pid.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_kdc_pid.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:1000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

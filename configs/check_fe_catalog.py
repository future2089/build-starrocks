import subprocess
script = r"""echo "=== hive_arm catalog in FE ==="
cat /proc/2634709/root/opt/starrocks/fe/log/fe.audit.log 2>/dev/null | grep -i "hive_arm\|catalog" | tail -10
echo "=== Check for create catalog ==="
grep -i "create.*catalog\|hive_arm" /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null | head -10
echo "=== fe.conf ==="
cat /proc/2634709/root/opt/starrocks/fe/conf/fe.conf 2>/dev/null
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_fe_catalog.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_fe_catalog.sh'], capture_output=True, text=True, timeout=10)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

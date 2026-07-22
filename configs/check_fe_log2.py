import subprocess

script = r"""echo "=== fe.log size ==="
ls -la /proc/2634709/root/opt/starrocks/fe/log/fe.log 2>/dev/null || echo "(no fe.log)"
echo "=== fe.out tail ==="
tail -30 /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null || echo "(no fe.out)"
echo "=== fe.log last lines ==="
tail -10 /proc/2634709/root/opt/starrocks/fe/log/fe.log 2>/dev/null || echo "(no fe.log)"
echo "=== FE conf ==="
cat /proc/2634709/root/opt/starrocks/fe/conf/fe.conf 2>/dev/null
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_fe_log2.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'bash /tmp/check_fe_log2.sh'],
    capture_output=True, text=True, timeout=10
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

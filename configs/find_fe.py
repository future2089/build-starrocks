import subprocess

script = r"""echo "=== Find FE ==="
find / -name "starrocks-fe*.jar" -o -name "fe.conf" 2>/dev/null | head -10
echo "=== FE process (full cmd) ==="
ps aux | grep -i "[f]e\|[s]tarrocks.*fe" | grep -v grep | head -5
echo "=== Check common locations ==="
ls -la /opt/starrocks/ 2>/dev/null || echo "no /opt/starrocks"
ls -la /data/deploy/starrocks/ 2>/dev/null | head -10
echo "=== Check deploy dirs ==="
ls -la /data/deploy/ 2>/dev/null | head -10
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/find_fe.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'bash < /tmp/find_fe.sh'],
    capture_output=True, text=True, timeout=30
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

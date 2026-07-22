import subprocess

script = r"""echo "=== Supervisor conf ==="
cat /data/deploy/starrocks/supervisor/supervisord.conf 2>/dev/null | head -60
echo "=== Check /data/deploy/starrocks ==="
ls -la /data/deploy/starrocks/ 2>/dev/null
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_supervisor.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'bash < /tmp/check_supervisor.sh'],
    capture_output=True, text=True, timeout=10
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

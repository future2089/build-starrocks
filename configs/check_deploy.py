import subprocess

# Quick check of deploy directories
r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'ls -la /data/deploy/; echo "---"; ls -la /data/deploy/starrocks/ 2>/dev/null || echo "no starrocks dir"'],
    capture_output=True, text=True, timeout=10
)
print(r.stdout.strip()[:500] or "(empty)")
print("ERR:", r.stderr.strip()[:200] if r.stderr else '')

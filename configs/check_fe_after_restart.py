import subprocess, time

# Wait for FE to start
time.sleep(10)

# Check FE process and port
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'sh', '-c',
     'ps aux | grep -i "starrocks" | grep -v grep | head -3; echo "---"; netstat -tlnp 2>/dev/null | grep 9030'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:500] if r.stdout else '(empty)')
print(r.stderr.strip()[:300] if r.stderr else '')

# Test if FE is responsive
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SELECT CURRENT_USER();'],
    capture_output=True, text=True, timeout=15
)
print("\n=== FE query ===")
print(r2.stdout.strip() if r2.stdout else '(empty)')
print(r2.stderr.strip()[:300] if r2.stderr else '')

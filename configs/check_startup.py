import subprocess

r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'ps', 'aux'],
    capture_output=True, text=True, timeout=10
)
print("=== Processes ===")
print(r.stdout.strip()[:800] if r.stdout else '(empty)')

r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'ls', '-la', '/opt/starrocks/fe/bin/'],
    capture_output=True, text=True, timeout=10
)
print("\n=== FE bin ===")
print(r2.stdout.strip()[:500] if r2.stdout else '(empty)')

r3 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'cat', '/opt/starrocks/fe/bin/start_fe.sh'],
    capture_output=True, text=True, timeout=10
)
print("\n=== start_fe.sh (head) ===")
for line in r3.stdout.split('\n')[:30]:
    if 'krb5' in line.lower() or 'java' in line.lower() or 'conf' in line.lower():
        print(line[:200])

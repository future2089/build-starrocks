import subprocess, sys

# Check what's running in hadoop-arm container
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'ssh root@192.168.0.181 "docker exec hadoop-arm ps aux"'],
    capture_output=True, text=True, timeout=20
)
print("=== hadoop-arm processes ===")
print(r.stdout.strip() or '(empty)')
print(r.stderr.strip()[:300] if r.stderr else '')

# Check hadoop and hive availability
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'ssh root@192.168.0.181 "docker exec hadoop-arm which hdfs 2>&1; docker exec hadoop-arm which hive 2>&1"'],
    capture_output=True, text=True, timeout=20
)
print("\n=== hadoop/hive paths ===")
print(r2.stdout.strip() or '(empty)')

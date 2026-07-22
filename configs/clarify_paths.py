import subprocess

# Check paths on host and in container
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'echo ===HOST===; ls -la /data/ 2>/dev/null; ls -la /data/bigdata 2>/dev/null; ls -la /data/package 2>/dev/null; echo ===CONTAINER===; docker exec hadoop-arm bash -c \"ls -la /data/ 2>/dev/null; ls -la /data/bigdata 2>/dev/null || true; ls -la /data/package 2>/dev/null || true; find / -name start-dfs.sh 2>/dev/null; find / -name hive 2>/dev/null | head\"' 2>&1",
    shell=True, capture_output=True, text=True, timeout=30
)
print(r.stdout.strip()[:2000])
print('STDERR:', r.stderr.strip()[:300] if r.stderr else '')

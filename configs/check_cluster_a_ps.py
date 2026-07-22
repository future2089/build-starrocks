import subprocess

r = subprocess.run(
    ["docker", "exec", "cluster_a", "bash", "-c", "ps aux | grep HiveMetaStore | grep -v grep"],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:3000])

import subprocess

r = subprocess.run(
    ["docker", "exec", "cluster_a", "bash", "-c", "cat /usr/local/hive/conf/hive-site.xml | grep -A1 -B1 -E 'kerberos|metastore.uris'"],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000])

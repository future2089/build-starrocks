import subprocess

r = subprocess.run(
    ["docker", "exec", "cluster_a", "bash", "-c", "grep -E 'kerberos|metastore.uris' /usr/local/hive/conf/hive-site.xml"],
    capture_output=True, text=True, timeout=15
)
print('cluster_a hive-site.xml:')
print(r.stdout.strip()[:1000])

r2 = subprocess.run(
    ["docker", "exec", "cluster_a", "bash", "-c", "ps aux | grep HiveMetaStore | grep -v grep"],
    capture_output=True, text=True, timeout=15
)
print('\ncluster_a HMS process:')
print(r2.stdout.strip()[:500])

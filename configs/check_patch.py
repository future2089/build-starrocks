import subprocess

# Extract and decompile HadoopExt
subprocess.run(['docker', 'exec', '-i', 'sr-deploy',
    'sh', '-c', 'cd /tmp && jar xf /opt/starrocks/fe/lib/starrocks-hadoop-ext.jar'],
    capture_output=True, text=True, timeout=15)
r = subprocess.run(['docker', 'exec', '-i', 'sr-deploy',
    'javap', '-p', '/tmp/com/starrocks/connector/hadoop/HadoopExt.class'],
    capture_output=True, text=True, timeout=15)
print("=== HadoopExt ===")
print(r.stdout)
print(r.stderr[:500] if r.stderr else '')

# Extract and decompile HiveMetaClient
subprocess.run(['docker', 'exec', '-i', 'sr-deploy',
    'sh', '-c', 'cd /tmp && jar xf /opt/starrocks/fe/lib/starrocks-fe.jar'],
    capture_output=True, text=True, timeout=15)
r2 = subprocess.run(['docker', 'exec', '-i', 'sr-deploy',
    'javap', '-p', '/tmp/com/starrocks/connector/hive/HiveMetaClient.class'],
    capture_output=True, text=True, timeout=15)
print("=== HiveMetaClient ===")
print(r2.stdout)
print(r2.stderr[:500] if r2.stderr else '')

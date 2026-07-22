import subprocess

# Check jar timestamp
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'ls', '-la', '/opt/starrocks/fe/lib/starrocks-fe.jar'],
    capture_output=True, text=True, timeout=10
)
print("Jar:", r.stdout.strip())

# Decompile to verify fix
subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'sh', '-c', 'cd /tmp && jar xf /opt/starrocks/fe/lib/starrocks-fe.jar'],
    capture_output=True, text=True, timeout=15
)
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'javap', '-p', '-c',
     '/tmp/com/starrocks/connector/hive/HiveMetaClient.class'],
    capture_output=True, text=True, timeout=15
)
# Find the createHiveMetaClient method
lines = r2.stdout.split('\n')
found = False
for i, line in enumerate(lines):
    if 'createHiveMetaClient' in line:
        found = True
        # Print next 50 lines
        for l in lines[i:i+50]:
            if 'loginPrincipal' in l or 'client.kerberos' in l or 'kerberos.principal' in l:
                print(l[:200])
        break

if not found:
    print("Method not found")
    print(r2.stdout[:500] if r2.stdout else '(empty)')
print("STDERR:", r2.stderr.strip()[:300] if r2.stderr else '')

import subprocess

r = subprocess.run(
    "docker exec sr-deploy javap -c -p -classpath /opt/starrocks/fe/lib/starrocks-fe.jar:/opt/starrocks/fe/lib/* com.starrocks.connector.hive.HiveMetaClient 2>&1",
    shell=True, capture_output=True, text=True, timeout=30
)

# Find the private constructor
lines = r.stdout.split('\n')
found_constructor = False
depth = 0
for i, line in enumerate(lines):
    if 'private com.starrocks.connector.hive.HiveMetaClient(org.apache.hadoop.hive.conf.HiveConf' in line:
        found_constructor = True
        print('Constructor found at line', i)
    if found_constructor:
        print(line[:200])
        if line.strip().startswith('}') and depth <= 0:
            break
        if '{' in line:
            depth += 1
        if '}' in line:
            depth -= 1
            if depth <= 0:
                print('...')
                break

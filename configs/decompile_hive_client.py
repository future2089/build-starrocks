import subprocess

r = subprocess.run(
    "docker exec sr-deploy javap -c -p -classpath /opt/starrocks/fe/lib/starrocks-fe.jar:/opt/starrocks/fe/lib/* com.starrocks.connector.hive.HiveMetaClient 2>&1",
    shell=True, capture_output=True, text=True, timeout=30
)
# Show lines containing kerberos/principal/keytab
for line in r.stdout.split('\n'):
    if any(kw in line.lower() for kw in ['kerberos', 'principal', 'keytab', 'sasl', 'METASTORE', 'getClient', 'RecyclableClient']):
        print(line[:200])

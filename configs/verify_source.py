c = open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/connector/hive/HiveMetaClient.java').read()
checks = [
    ("HadoopExt import", "import com.starrocks.connector.hadoop.HadoopExt;"),
    ("GenericExceptionAction import", "import com.starrocks.connector.hadoop.GenericExceptionAction;"),
    ("krb5ConfPath field", "private final String krb5ConfPath;"),
    ("loginPrincipal with client.kerberos.principal", 'properties.get("hive.metastore.client.kerberos.principal")'),
    ("fallback to kerberos.principal", 'loginPrincipal = properties.get("hive.metastore.kerberos.principal")'),
    ("doAsWithSwap in getClient", "doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath"),
    ("doAsWithSwap in callRPC", "HadoopExt.getInstance().doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath,"),
    ("method.invoke inside doAs", "return (T) method.invoke(hiveClient, args);"),
]
ok = True
for name, pattern in checks:
    found = pattern in c
    if not found:
        print(f"FAIL: {name}")
        ok = False
    else:
        print(f"OK: {name}")
if ok:
    print("\nAll checks passed")

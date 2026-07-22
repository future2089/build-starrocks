"""Apply the HiveMetaClient patch to the file, with the login principal fix."""
import re, os

filepath = "/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/connector/hive/HiveMetaClient.java"

with open(filepath, 'r') as f:
    content = f.read()

changes = 0

# 1. Add imports after line with "import com.starrocks.connector.exception.StarRocksConnectorException;"
old = "import com.starrocks.connector.exception.StarRocksConnectorException;"
new = "import com.starrocks.connector.exception.StarRocksConnectorException;\nimport com.starrocks.connector.hadoop.HadoopExt;\nimport com.starrocks.connector.hadoop.GenericExceptionAction;"
if old in content and "import com.starrocks.connector.hadoop.HadoopExt;" not in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("1. Added imports")

# 2. Add fields after "private final HiveConf conf;"
old = "    private final HiveConf conf;\n"
new = old + "    private final String krbPrincipal;\n    private final String krbKeytab;\n    private final String krb5ConfPath;\n"
if old in content and "krbPrincipal" not in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("2. Added krb fields")

# 3. Modify constructors
old = "    public HiveMetaClient(HiveConf conf) {\n        this.conf = conf;\n    }"
new = """    public HiveMetaClient(HiveConf conf) {
        this(conf, null, null, null);
    }

    public HiveMetaClient(HiveConf conf, String krbPrincipal, String krbKeytab, String krb5ConfPath) {
        this.conf = conf;
        this.krbPrincipal = krbPrincipal;
        this.krbKeytab = krbKeytab;
        this.krb5ConfPath = krb5ConfPath;
    }"""
if old in content and "this.krbPrincipal" not in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("3. Modified constructors")

# 4. Modify createHiveMetaClient return (with login principal fix)
old = "        return new HiveMetaClient(conf);"
new = """        String loginPrincipal = properties.get("hive.metastore.client.kerberos.principal");
        if (loginPrincipal == null) {
            loginPrincipal = properties.get("hive.metastore.kerberos.principal");
        }
        return new HiveMetaClient(conf,
                loginPrincipal,
                properties.get("hive.metastore.kerberos.keytab"),
                properties.get("hive.metastore.kerberos.krb5.conf"));"""
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("4. Modified createHiveMetaClient with login principal fix")

# 5. Modify getClient() to use doAsWithSwap
old = """        synchronized (clientPoolLock) {
            RecyclableClient client = clientPool.poll();
            // The pool was empty so create a new client and return that.
            // Serialize client creation to defend against possible race conditions accessing
            // local Kerberos state
            if (client == null) {
                return new RecyclableClient(conf);
            } else {
                return client;
            }
        }"""
new = """        synchronized (clientPoolLock) {
            RecyclableClient client = clientPool.poll();
            if (client == null) {
                if (krbPrincipal != null && krbKeytab != null) {
                    try {
                        return HadoopExt.getInstance().doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath,
                            new GenericExceptionAction<RecyclableClient, Exception>() {
                                @Override
                                public RecyclableClient run() throws Exception {
                                    return new RecyclableClient(conf);
                                }
                            });
                    } catch (Exception e) {
                        throw new MetaException("Kerberos login failed: " + e.getMessage());
                    }
                }
                return new RecyclableClient(conf);
            } else {
                return client;
            }
        }"""
if old in content and "doAsWithSwap" not in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("5. Modified getClient() with doAsWithSwap")

# 6. Modify callRPC() to use doAsWithSwap
old = """            client = getClient();
            argClasses = argClasses == null ? ClassUtils.getCompatibleParamClasses(args) : argClasses;
            Method method = client.hiveClient.getClass().getDeclaredMethod(methodName, argClasses);
            return (T) method.invoke(client.hiveClient, args);"""
new = """            client = getClient();
            argClasses = argClasses == null ? ClassUtils.getCompatibleParamClasses(args) : argClasses;
            Method method = client.hiveClient.getClass().getDeclaredMethod(methodName, argClasses);
            IMetaStoreClient hiveClient = client.hiveClient;
            return HadoopExt.getInstance().doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath,
                new GenericExceptionAction<T, Exception>() {
                    @Override
                    public T run() throws Exception {
                        return (T) method.invoke(hiveClient, args);
                    }
                });"""
if old in content and "IMetaStoreClient hiveClient" not in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("6. Modified callRPC() with doAsWithSwap")

with open(filepath, 'w') as f:
    f.write(content)

print(f"\nTotal changes: {changes}")

# Verify the result
with open(filepath, 'r') as f:
    c = f.read()

# Check key indicators
checks = [
    ("HadoopExt import", "import com.starrocks.connector.hadoop.HadoopExt;"),
    ("krb5ConfPath field", "private final String krb5ConfPath;"),
    ("loginPrincipal", "loginPrincipal = properties.get(\"hive.metastore.kerberos.principal\");"),
    ("client.kerberos.principal", "properties.get(\"hive.metastore.client.kerberos.principal\")"),
    ("doAsWithSwap in getClient", "doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath"),
    ("doAsWithSwap in callRPC", "doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath"),
]
for name, pattern in checks:
    found = pattern in c
    print(f"  {'✅' if found else '❌'} {name}")

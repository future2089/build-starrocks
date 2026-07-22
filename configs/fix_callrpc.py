f = open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/connector/hive/HiveMetaClient.java', 'r')
c = f.read()
f.close()

old = """            Method method = client.hiveClient.getClass().getDeclaredMethod(methodName, argClasses);
            return (T) method.invoke(client.hiveClient, args);"""

new = """            Method method = client.hiveClient.getClass().getDeclaredMethod(methodName, argClasses);
            IMetaStoreClient hiveClient = client.hiveClient;
            return HadoopExt.getInstance().doAsWithSwap(krbPrincipal, krbKeytab, krb5ConfPath,
                new GenericExceptionAction<T, Exception>() {
                    @Override
                    public T run() throws Exception {
                        return (T) method.invoke(hiveClient, args);
                    }
                });"""

if old in c:
    c = c.replace(old, new, 1)
    with open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/connector/hive/HiveMetaClient.java', 'w') as f:
        f.write(c)
    print('SUCCESS: callRPC patched with doAsWithSwap')
else:
    print('ERROR: old text not found')
    idx = c.find('method.invoke')
    if idx >= 0:
        print(repr(c[idx-50:idx+100]))
    else:
        print('method.invoke not found at all')

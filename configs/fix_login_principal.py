import re

filepath = "/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/connector/hive/HiveMetaClient.java"
with open(filepath, 'r') as f:
    content = f.read()

old_text = """        return new HiveMetaClient(conf,
                properties.get("hive.metastore.kerberos.principal"),
                properties.get("hive.metastore.kerberos.keytab"),
                properties.get("hive.metastore.kerberos.krb5.conf"));"""

new_text = """        String loginPrincipal = properties.get("hive.metastore.client.kerberos.principal");
        if (loginPrincipal == null) {
            loginPrincipal = properties.get("hive.metastore.kerberos.principal");
        }
        return new HiveMetaClient(conf,
                loginPrincipal,
                properties.get("hive.metastore.kerberos.keytab"),
                properties.get("hive.metastore.kerberos.krb5.conf"));"""

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    with open(filepath, 'w') as f:
        f.write(content)
    print("SUCCESS: login principal fixed")
else:
    print("ERROR: old text not found!")
    idx = content.find("return new HiveMetaClient")
    if idx >= 0:
        print("Found at index", idx)
        print(repr(content[idx:idx+250]))
    else:
        print("'return new HiveMetaClient' not found in file")

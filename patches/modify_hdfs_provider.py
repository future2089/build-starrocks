with open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/credential/hdfs/HDFSCloudConfigurationProvider.java', 'r') as f:
    content = f.read()

old = """        HDFSCloudCredential hdfsCloudCredential = new HDFSCloudCredential(
                getOrDefault(properties, HDFS_AUTHENTICATION),
                getOrDefault(properties, HDFS_USERNAME, HDFS_USERNAME_DEPRECATED),
                getOrDefault(properties, HDFS_PASSWORD, HDFS_PASSWORD_DEPRECATED),
                getOrDefault(properties, HDFS_KERBEROS_PRINCIPAL, HDFS_KERBEROS_PRINCIPAL_DEPRECATED),
                getOrDefault(properties, HADOOP_KERBEROS_KEYTAB, HDFS_KERBEROS_KEYTAB_DEPRECATED),
                getOrDefault(properties, HADOOP_KERBEROS_KEYTAB_CONTENT, HDFS_KERBEROS_KEYTAB_CONTENT_DEPRECATED),
                prop
        );"""

new = """        // Support standard Hadoop config keys (hadoop.security.krb5.principal,
        // hadoop.security.keytab.file) as fallback for FE credential validation,
        // so that users can use standard Hadoop config keys in catalog properties.
        String krbPrincipal = getOrDefault(properties, HDFS_KERBEROS_PRINCIPAL, HDFS_KERBEROS_PRINCIPAL_DEPRECATED);
        if (krbPrincipal.isEmpty()) {
            krbPrincipal = properties.getOrDefault("hadoop.security.krb5.principal", "");
        }
        String krbKeytab = getOrDefault(properties, HADOOP_KERBEROS_KEYTAB, HDFS_KERBEROS_KEYTAB_DEPRECATED);
        if (krbKeytab.isEmpty()) {
            krbKeytab = properties.getOrDefault("hadoop.security.keytab.file", "");
        }
        HDFSCloudCredential hdfsCloudCredential = new HDFSCloudCredential(
                getOrDefault(properties, HDFS_AUTHENTICATION),
                getOrDefault(properties, HDFS_USERNAME, HDFS_USERNAME_DEPRECATED),
                getOrDefault(properties, HDFS_PASSWORD, HDFS_PASSWORD_DEPRECATED),
                krbPrincipal,
                krbKeytab,
                getOrDefault(properties, HADOOP_KERBEROS_KEYTAB_CONTENT, HDFS_KERBEROS_KEYTAB_CONTENT_DEPRECATED),
                prop
        );"""

if old in content:
    content = content.replace(old, new)
    with open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/credential/hdfs/HDFSCloudConfigurationProvider.java', 'w') as f:
        f.write(content)
    print('SUCCESS: HDFSCloudConfigurationProvider modified')
else:
    print('ERROR: Could not find target text')
    import sys
    idx = content.find('HDFSCloudCredential hdfsCloudCredential')
    if idx >= 0:
        print('Found at position', idx)
        print(content[idx:idx+600])

with open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/credential/hdfs/HDFSCloudCredential.java', 'r') as f:
    content = f.read()

old = """    @Override
    public void toThrift(Map<String, String> properties) {
        if (hadoopConfiguration == null || hadoopConfiguration.isEmpty()) {
            return;
        }
        // Forward HDFS HA configuration from catalog properties to BE
        // Properties like dfs.nameservices, dfs.ha.namenodes.*,
        // dfs.namenode.rpc-address.*, dfs.client.failover.proxy.provider.*
        // need to be sent to the BE for proper HDFS HA connectivity.
        for (Map.Entry<String, String> entry : hadoopConfiguration.entrySet()) {"""

new = """    @Override
    public void toThrift(Map<String, String> properties) {
        // Forward FE's Kerberos auth config to BE even though hadoop.security.authentication
        // is removed from hadoopConfiguration by preprocessProperties().
        if (KERBEROS_AUTH.equals(authentication)) {
            properties.put("hadoop.security.authentication", "kerberos");
            if (!krbKeyTabFile.isEmpty()) {
                properties.put("hadoop.security.keytab.file", krbKeyTabFile);
            }
            if (!krbPrincipal.isEmpty()) {
                properties.put("hadoop.security.krb5.principal", krbPrincipal);
            }
        }
        if (hadoopConfiguration == null || hadoopConfiguration.isEmpty()) {
            return;
        }
        // Forward HDFS HA/Kerberos configuration from catalog properties to BE.
        // Properties like dfs.nameservices, dfs.ha.namenodes.*,
        // dfs.namenode.rpc-address.*, dfs.client.failover.proxy.provider.*,
        // hadoop.security.* need to be sent to the BE for proper connectivity.
        for (Map.Entry<String, String> entry : hadoopConfiguration.entrySet()) {"""

if old in content:
    content = content.replace(old, new)
    with open('/data/starrocks-build/starrocks-3.3.17/fe/fe-core/src/main/java/com/starrocks/credential/hdfs/HDFSCloudCredential.java', 'w') as f:
        f.write(content)
    print('SUCCESS: toThrift modified')
else:
    print('ERROR: Could not find target text')
    idx = content.find('public void toThrift')
    if idx >= 0:
        print('Found at:', idx)
        print(content[idx:idx+500])

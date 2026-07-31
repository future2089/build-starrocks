// Copyright 2021-present StarRocks, Inc. All rights reserved.
// [Original license header]
package com.starrocks.connector.hive;

import com.google.common.collect.Lists;
import com.starrocks.common.Config;
import com.starrocks.common.profile.Timer;
import com.starrocks.common.profile.Tracers;
import com.starrocks.connector.HdfsEnvironment;
import com.starrocks.connector.exception.StarRocksConnectorException;
import com.starrocks.connector.hadoop.HadoopExt;
import com.starrocks.connector.hadoop.GenericExceptionAction;
// ... other imports remain the same ...

public class HiveMetaClient {
    // ... existing fields ...
    private final HiveConf conf;
    private final String krbPrincipal;  // NEW
    private final String krbKeytab;     // NEW

    // NEW: Constructor with Kerberos parameters
    public HiveMetaClient(HiveConf conf) { this(conf, null, null); }

    public HiveMetaClient(HiveConf conf, String krbPrincipal, String krbKeytab) {
        this.conf = conf;
        this.krbPrincipal = krbPrincipal;
        this.krbKeytab = krbKeytab;
    }

    // NEW: Read Kerberos config from properties
    public static HiveMetaClient createHiveMetaClient(HdfsEnvironment env, Map<String, String> properties) {
        HiveConf conf = new HiveConf();
        conf.addResource(env.getConfiguration());
        properties.forEach(conf::set);
        if (properties.containsKey(HIVE_METASTORE_URIS)) {
            conf.set(MetastoreConf.ConfVars.THRIFT_URIS.getHiveName(), properties.get(HIVE_METASTORE_URIS));
        }
        String hmsTimeout = properties.getOrDefault(HIVE_METASTORE_TIMEOUT, String.valueOf(Config.hive_meta_store_timeout_s));
        conf.set(MetastoreConf.ConfVars.CLIENT_SOCKET_TIMEOUT.getHiveName(), hmsTimeout);
        return new HiveMetaClient(conf,
                properties.get("hive.metastore.kerberos.principal"),
                properties.get("hive.metastore.kerberos.keytab"));
    }

    // ... existing code ...

    // MODIFIED: callRPC with Kerberos UGI switching
    public <T> T callRPC(String methodName, String messageIfError, Class<?>[] argClasses, Object... args) {
        RecyclableClient client = null;
        StarRocksConnectorException connectionException = null;
        try {
            client = getClient();
            argClasses = argClasses == null ? ClassUtils.getCompatibleParamClasses(args) : argClasses;
            Method method = client.hiveClient.getClass().getDeclaredMethod(methodName, argClasses);
            IMetaStoreClient hiveClient = client.hiveClient;
            return HadoopExt.getInstance().doAsWithSwap(krbPrincipal, krbKeytab,
                new GenericExceptionAction<T, Exception>() {
                    @Override
                    public T run() throws Exception {
                        return (T) method.invoke(hiveClient, args);
                    }
                });
        } catch (Throwable e) {
            LOG.error(messageIfError, e);
            connectionException = new StarRocksConnectorException(messageIfError + ", msg: " +
                    ExceptionUtils.getRootCauseMessage(e), e);
            throw connectionException;
        } finally {
            // ... existing cleanup code ...
        }
    }

    // ... rest of the class methods unchanged ...
}

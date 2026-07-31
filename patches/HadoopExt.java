// Copyright 2021-present StarRocks, Inc. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package com.starrocks.connector.hadoop;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.security.UserGroupInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.security.PrivilegedAction;
import java.lang.reflect.Method;
import java.io.File;
import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;

public class HadoopExt {
    private static final Logger LOGGER = LoggerFactory.getLogger(HadoopExt.class);
    private static final HadoopExt INSTANCE = new HadoopExt();
    public static final String LOGGER_MESSAGE_PREFIX = "[hadoop-ext]";
    public static final String HADOOP_CONFIG_RESOURCES = "hadoop.config.resources";
    public static final String HADOOP_RUNTIME_JARS = "hadoop.runtime.jars";
    public static final String HADOOP_CLOUD_CONFIGURATION_STRING = "hadoop.cloud.configuration.string";
    public static final String HADOOP_USERNAME = "hadoop.username";

    // ---- per-catalog HDFS credential keys (forwarded from FE catalog properties) ----
    private static final String[] PRINCIPAL_KEYS = new String[] {
            "hadoop.kerberos.principal",
            "hadoop.security.krb5.principal",
            "hdfs.kerberos.principal"
    };
    private static final String[] KEYTAB_KEYS = new String[] {
            "hadoop.kerberos.keytab",
            "hadoop.security.keytab.file",
            "hdfs.kerberos.keytab"
    };
    private static final String TICKET_CACHE_KEY = "hadoop.security.kerberos.ticket.cache.path";

    // Cache of per-catalog UGIs. Key = principal + "@@" + keytab (or "cc:" + cachePath).
    // Each entry is an independent UGI, NOT the JVM-wide loginUser, so multiple
    // secured Hadoop clusters (different realms) can be accessed concurrently.
    private static final ConcurrentHashMap<String, UserGroupInformation> HDFS_UGI_CACHE = new ConcurrentHashMap<>();

    public static HadoopExt getInstance() { return INSTANCE; }

    public void rewriteConfiguration(Configuration conf) {}
    public FileSystem bindUGIToFileSystem(FileSystem fs, UserGroupInformation ugi) { return fs; }
    public String getCloudConfString(Configuration conf) { return conf.get(HADOOP_CLOUD_CONFIGURATION_STRING, ""); }
    public UserGroupInformation getHMSUGI(Configuration conf) { return null; }

    /**
     * Build a per-catalog UGI for HDFS access.
     *
     * StarRocks' patched {@code FileSystem.createFileSystem()} calls this hook and, when a
     * non-null UGI is returned, creates the FileSystem inside {@code ugi.doAs(...)}. The
     * resulting DFSClient/RPC proxy is permanently bound to that UGI, which gives us true
     * per-catalog Kerberos identity isolation on the BE side without touching the JVM-wide
     * login user (which is shared and can only hold one realm at a time).
     *
     * Preference order:
     *   1. keytab + principal  -> loginUserFromKeytabAndReturnUGI (self-renewing, recommended)
     *   2. ticket cache path   -> getUGIFromTicketCache (requires an external kinit daemon)
     *   3. null                -> fall back to the default global UGI (original behaviour)
     */
    public UserGroupInformation getHDFSUGI(Configuration conf) {
        if (conf == null) {
            return null;
        }
        String principal = firstNonEmpty(conf, PRINCIPAL_KEYS);
        String keytab = firstNonEmpty(conf, KEYTAB_KEYS);
        String ticketCache = emptyToNull(conf.get(TICKET_CACHE_KEY));

        if (principal == null && ticketCache == null) {
            return null;
        }

        try {
            if (principal != null && keytab != null && new File(keytab).exists()) {
                return getOrCreateKeytabUGI(principal, keytab, "HDFS");
            }

            if (ticketCache != null) {
                ensureKerberosEnabled();
                UserGroupInformation ugi = UserGroupInformation.getUGIFromTicketCache(ticketCache, null);
                LOGGER.info("{} created per-catalog HDFS UGI from ticket cache {}, user={}",
                        LOGGER_MESSAGE_PREFIX, ticketCache, ugi.getUserName());
                return ugi;
            }
        } catch (Throwable t) {
            LOGGER.warn("{} failed to build per-catalog HDFS UGI (principal={}, keytab={}, ticketCache={}), "
                    + "falling back to the global login user", LOGGER_MESSAGE_PREFIX, principal, keytab, ticketCache, t);
            System.err.println(LOGGER_MESSAGE_PREFIX + " failed to build per-catalog HDFS UGI: " + t);
        }
        return null;
    }

    /**
     * Get (or lazily create) an isolated UGI logged in from the given keytab.
     *
     * Uses {@code loginUserFromKeytabAndReturnUGI}, which returns a standalone UGI and
     * does NOT overwrite the JVM-wide login user. This is what allows several Kerberos
     * realms to be used concurrently inside one JVM. Entries are cached per
     * principal+keytab and refreshed via {@code checkTGTAndReloginFromKeytab()}.
     *
     * Returns null if login fails, so callers can fall back to their legacy behaviour.
     */
    private static UserGroupInformation getOrCreateKeytabUGI(String principal, String keytab, String usage) {
        final String cacheKey = principal + "@@" + keytab;
        UserGroupInformation ugi = HDFS_UGI_CACHE.get(cacheKey);
        if (ugi == null) {
            synchronized (HDFS_UGI_CACHE) {
                ugi = HDFS_UGI_CACHE.get(cacheKey);
                if (ugi == null) {
                    try {
                        ensureKerberosEnabled();
                        ugi = UserGroupInformation.loginUserFromKeytabAndReturnUGI(principal, keytab);
                    } catch (IOException e) {
                        LOGGER.warn("{} keytab login failed for {} ({})", LOGGER_MESSAGE_PREFIX, principal, usage, e);
                        return null;
                    }
                    HDFS_UGI_CACHE.put(cacheKey, ugi);
                    LOGGER.info("{} created per-catalog {} UGI from keytab, principal={}",
                            LOGGER_MESSAGE_PREFIX, usage, principal);
                    System.err.println(LOGGER_MESSAGE_PREFIX
                            + " created per-catalog " + usage + " UGI from keytab, principal=" + principal);
                }
            }
        } else {
            try {
                ugi.checkTGTAndReloginFromKeytab();
            } catch (IOException relogin) {
                LOGGER.warn("{} relogin from keytab failed for {}", LOGGER_MESSAGE_PREFIX, principal, relogin);
            }
        }
        return ugi;
    }

    /**
     * True when switching to {@code krb5ConfPath} would be a no-op, i.e. it is null or
     * already resolves to the file the JVM is currently using. In that case we can skip
     * the global krb5.conf swap (and the lock that protects it) entirely.
     */
    private static boolean canSkipKrb5Swap(String krb5ConfPath) {
        if (krb5ConfPath == null) {
            return true;
        }
        String current = System.getProperty("java.security.krb5.conf");
        if (current == null) {
            return false;
        }
        if (krb5ConfPath.equals(current)) {
            return true;
        }
        try {
            return new File(krb5ConfPath).getCanonicalFile()
                    .equals(new File(current).getCanonicalFile());
        } catch (IOException e) {
            return false;
        }
    }

    private static void ensureKerberosEnabled() {
        if (!UserGroupInformation.isSecurityEnabled()) {
            Configuration ugiConf = new Configuration();
            ugiConf.set("hadoop.security.authentication", "kerberos");
            UserGroupInformation.setConfiguration(ugiConf);
        }
    }

    private static String firstNonEmpty(Configuration conf, String[] keys) {
        for (String key : keys) {
            String v = emptyToNull(conf.get(key));
            if (v != null) {
                return v;
            }
        }
        return null;
    }

    private static String emptyToNull(String v) {
        if (v == null) {
            return null;
        }
        v = v.trim();
        return v.isEmpty() ? null : v;
    }

    // Per-catalog Kerberos UGI switching with dynamic krb5.conf support
    public <R, E extends Exception> R doAsWithSwap(String krbPrincipal, String krbKeytab,
                                                      GenericExceptionAction<R, E> action) throws E {
        return doAsWithSwap(krbPrincipal, krbKeytab, null, action);
    }

    /**
     * Run {@code action} as the given Kerberos identity.
     *
     * FAST PATH: taken when no real krb5.conf swap is required, i.e. krb5ConfPath is
     * null or already identical to the JVM-wide {@code java.security.krb5.conf}. We then
     * use a cached, isolated UGI from {@code loginUserFromKeytabAndReturnUGI} -- no
     * global lock and no mutation of the JVM login user, so metadata calls against
     * different catalogs (and different realms) run fully in parallel.
     *
     * This is the recommended multi-cluster setup: one krb5.conf containing every realm
     * plus the matching [domain_realm] host mappings. Hive SASL normalises the service
     * principal to a hostbased form (hive/hive-c@EXAMPLE.COM -> hive@hive-c, realm
     * dropped), so the realm is resolved from [domain_realm] anyway -- a per-catalog
     * krb5.conf buys nothing and costs full serialization.
     *
     * SLOW PATH: krb5ConfPath genuinely differs from the current one. Swapping it
     * mutates a JVM-wide system property and the global login user, so it must stay
     * serialized. Kept for compatibility; also used as fallback if keytab login fails.
     */
    public <R, E extends Exception> R doAsWithSwap(String krbPrincipal, String krbKeytab,
                                                      String krb5ConfPath,
                                                      GenericExceptionAction<R, E> action) throws E {
        if (krbPrincipal == null || krbKeytab == null) {
            return action.run();
        }

        if (canSkipKrb5Swap(krb5ConfPath) && new File(krbKeytab).exists()) {
            UserGroupInformation ugi = getOrCreateKeytabUGI(krbPrincipal, krbKeytab, "HMS");
            if (ugi != null) {
                return executeActionInDoAs(ugi, action);
            }
            // login failed -> fall through to the legacy serialized path
        }

        synchronized (UserGroupInformation.class) {
            String origKrb5Conf = null;
            try {
                if (krb5ConfPath != null) {
                    origKrb5Conf = System.getProperty("java.security.krb5.conf");
                    System.setProperty("java.security.krb5.conf", krb5ConfPath);
                    refreshKrb5Config();
                }
                ensureKerberosEnabled();
                UserGroupInformation.loginUserFromKeytab(krbPrincipal, krbKeytab);
                UserGroupInformation ugi = UserGroupInformation.getLoginUser();
                return executeActionInDoAs(ugi, action);
            } catch (IOException e) {
                throw new RuntimeException("Kerberos login failed for " + krbPrincipal, e);
            } finally {
                if (krb5ConfPath != null && origKrb5Conf != null) {
                    System.setProperty("java.security.krb5.conf", origKrb5Conf);
                    refreshKrb5Config();
                }
            }
        }
    }

    public <R, E extends Exception> R doAs(UserGroupInformation ugi, GenericExceptionAction<R, E> action) throws E {
        if (ugi == null) { return action.run(); }
        return executeActionInDoAs(ugi, action);
    }

    private static void refreshKrb5Config() {
        try {
            Class<?> configClass = Class.forName("sun.security.krb5.Config");
            Method refreshMethod = configClass.getMethod("refresh");
            refreshMethod.invoke(null);
        } catch (Exception e) {
            LOGGER.warn("Failed to refresh Krb5 config", e);
        }
    }

    static <R, E extends Exception> R executeActionInDoAs(UserGroupInformation userGroupInformation,
                                                          GenericExceptionAction<R, E> action) throws E {
        return userGroupInformation.doAs((PrivilegedAction<ResultOrException<R, E>>) () -> {
            try {
                return new ResultOrException<>(action.run(), null);
            } catch (Throwable e) {
                return new ResultOrException<>(null, e);
            }
        }).get();
    }

    private static class ResultOrException<T, E extends Exception> {
        private final T result;
        private final Throwable exception;
        public ResultOrException(T result, Throwable exception) { this.result = result; this.exception = exception; }
        @SuppressWarnings("unchecked")
        public T get() throws E {
            if (exception != null) {
                if (exception instanceof Error) throw (Error) exception;
                if (exception instanceof RuntimeException) throw (RuntimeException) exception;
                throw (E) exception;
            }
            return result;
        }
    }
}

// Copyright 2021-present StarRocks, Inc. All rights reserved.
// ...
// [Original license header - truncated for brevity]
package com.starrocks.connector.hadoop;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.security.UserGroupInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.security.PrivilegedAction;
import java.io.IOException;

public class HadoopExt {
    private static final Logger LOGGER = LoggerFactory.getLogger(HadoopExt.class);
    private static final HadoopExt INSTANCE = new HadoopExt();
    public static final String LOGGER_MESSAGE_PREFIX = "[hadoop-ext]";
    public static final String HADOOP_CONFIG_RESOURCES = "hadoop.config.resources";
    public static final String HADOOP_RUNTIME_JARS = "hadoop.runtime.jars";
    public static final String HADOOP_CLOUD_CONFIGURATION_STRING = "hadoop.cloud.configuration.string";
    public static final String HADOOP_USERNAME = "hadoop.username";

    public static HadoopExt getInstance() { return INSTANCE; }

    public void rewriteConfiguration(Configuration conf) {}
    public FileSystem bindUGIToFileSystem(FileSystem fs, UserGroupInformation ugi) { return fs; }
    public String getCloudConfString(Configuration conf) { return conf.get(HADOOP_CLOUD_CONFIGURATION_STRING, ""); }
    public UserGroupInformation getHMSUGI(Configuration conf) { return null; }
    public UserGroupInformation getHDFSUGI(Configuration conf) { return null; }

    // === NEW: Per-catalog Kerberos UGI switching ===
    public <R, E extends Exception> R doAsWithSwap(String krbPrincipal, String krbKeytab,
                                                      GenericExceptionAction<R, E> action) throws E {
        if (krbPrincipal == null || krbKeytab == null) {
            return action.run();
        }
        synchronized (UserGroupInformation.class) {
            try {
                UserGroupInformation.loginUserFromKeytab(krbPrincipal, krbKeytab);
                UserGroupInformation ugi = UserGroupInformation.getLoginUser();
                return executeActionInDoAs(ugi, action);
            } catch (IOException e) {
                throw new RuntimeException("Kerberos login failed for " + krbPrincipal, e);
            }
        }
    }

    public <R, E extends Exception> R doAs(UserGroupInformation ugi, GenericExceptionAction<R, E> action) throws E {
        if (ugi == null) { return action.run(); }
        return executeActionInDoAs(ugi, action);
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

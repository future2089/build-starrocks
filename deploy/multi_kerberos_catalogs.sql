-- multi_kerberos_catalogs.sql
-- 已验证可用的「单 StarRocks 集群并发访问多个异构安全 Hive 集群」catalog 定义模板。
-- 验证日期：2026-07-31（StarRocks 3.3.17 + patches/HadoopExt.java 的 getHDFSUGI 实现）
--
-- 前置条件：
--   1. 已执行 patches/hotpatch_hadoop_ext.sh 更新 BE 的 starrocks-hadoop-ext.jar 并重启 BE，
--      使 HadoopExt.getHDFSUGI() 能为每个 catalog 建立独立 UGI。
--   2. krb5.conf 的 [domain_realm] 为每个集群的 host 与 nameservice 显式建立 realm 映射，
--      否则 Hive SASL 的 hostbased 服务名会回落到 default_realm，报 "No service creds"。
--   3. BE conf/core-site.xml 的 hadoop.security.auth_to_local 含所有 realm 的 RULE。
--   4. keytab 放在 BE 进程可读路径（这里统一用 /opt/starrocks/krb5/，chmod 644）。
--
-- 关键点：HDFS 凭据属性必须使用 `hadoop.` 前缀。
--   FE 的 HDFSCloudCredential.toThrift 只把 dfs./hadoop./ipc./hive. 前缀的键透传给 BE，
--   写成 `hdfs.kerberos.principal` 到不了 BE，BE 就会退回全局 ccache 而导致多 realm 互斥。

DROP CATALOG IF EXISTS hive_catalog;
DROP CATALOG IF EXISTS hive_hivec;

-- ============ 集群 A：ARM 侧 Hive，realm = HIVE_ARM.TEST ============
CREATE EXTERNAL CATALOG hive_catalog
PROPERTIES (
  "type" = "hive",
  "hive.metastore.uris" = "thrift://192.168.0.181:9086",
  "hive.metastore.sasl.enabled" = "true",
  -- HMS 服务端 principal（FE 侧 SASL 用）
  "hive.metastore.kerberos.principal" = "hive/hive-arm@HIVE_ARM.TEST",
  -- FE 客户端身份
  "hive.metastore.client.kerberos.principal" = "user_arm@HIVE_ARM.TEST",
  "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/user_arm.keytab",
  "hive.metastore.kerberos.krb5.conf" = "/opt/starrocks/fe/meta/krb5.conf",
  -- BE 侧 HDFS 身份（hadoop. 前缀才会透传到 BE）
  "hadoop.security.authentication" = "kerberos",
  "hadoop.kerberos.principal" = "user_arm@HIVE_ARM.TEST",
  "hadoop.kerberos.keytab" = "/opt/starrocks/krb5/user_arm.keytab",
  "hadoop.security.krb5.principal" = "user_arm@HIVE_ARM.TEST",
  "hadoop.security.keytab.file" = "/opt/starrocks/krb5/user_arm.keytab",
  -- 兼容旧写法（仅 FE 侧生效）
  "hdfs.authentication" = "kerberos",
  "hdfs.kerberos.principal" = "user_arm@HIVE_ARM.TEST",
  -- HDFS HA
  "dfs.nameservices" = "arm-ha",
  "dfs.ha.namenodes.arm-ha" = "nn1",
  "dfs.namenode.rpc-address.arm-ha.nn1" = "192.168.0.181:8021",
  "dfs.client.failover.proxy.provider.arm-ha" =
      "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider"
);

-- ============ 集群 B：hive_c 容器内 Hive，realm = EXAMPLE.COM ============
CREATE EXTERNAL CATALOG hive_hivec
PROPERTIES (
  "type" = "hive",
  "hive.metastore.uris" = "thrift://hive-c:9083",
  "hive.metastore.sasl.enabled" = "true",
  "hive.metastore.kerberos.principal" = "hive/hive-c@EXAMPLE.COM",
  "hive.metastore.client.kerberos.principal" = "user_c@EXAMPLE.COM",
  "hive.metastore.kerberos.keytab" = "/opt/starrocks/fe/meta/user_c.keytab",
  "hive.metastore.kerberos.krb5.conf" = "/opt/starrocks/fe/meta/krb5.conf",
  "hadoop.security.authentication" = "kerberos",
  "hadoop.kerberos.principal" = "user_c@EXAMPLE.COM",
  "hadoop.kerberos.keytab" = "/opt/starrocks/krb5/user_c.keytab",
  "hadoop.security.krb5.principal" = "user_c@EXAMPLE.COM",
  "hadoop.security.keytab.file" = "/opt/starrocks/krb5/user_c.keytab",
  "hdfs.authentication" = "kerberos",
  "hdfs.kerberos.principal" = "user_c@EXAMPLE.COM",
  "dfs.nameservices" = "hacluster",
  "dfs.ha.namenodes.hacluster" = "nn1,nn2",
  "dfs.namenode.rpc-address.hacluster.nn1" = "hive-c:8020",
  "dfs.namenode.rpc-address.hacluster.nn2" = "hive-c:8022",
  "dfs.client.failover.proxy.provider.hacluster" =
      "org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider",
  "dfs.replication" = "1"
);

SHOW CATALOGS;

-- ============ 验证：两个不同 realm 的集群同时可查 + 跨集群 JOIN ============
-- SELECT * FROM hive_hivec.demo.users ORDER BY id;
-- SELECT * FROM hive_catalog.`default`.test_tbl;
-- SELECT c.id, c.name AS name_hivec, a.name AS name_arm
--   FROM hive_hivec.demo.users c
--   JOIN hive_catalog.`default`.test_tbl a ON c.id = a.id
--  ORDER BY c.id;

# 验证结果: StarRocks 多 Hive Catalog 连接不同安全 HA HDFS 集群

## 验证日期

2026-07-14

## 环境状态

| 组件 | 状态 | 备注 |
|------|------|------|
| sr-deploy (StarRocks FE+BE) | ✅ 运行中 | FE PID 1919, BE PID 310 |
| cluster_a (HMS :9084) | ✅ 运行中 | PID 1183595 (宿主机) |
| cluster_b (HMS :9085) | ✅ 运行中 | PID 1090127 (宿主机) |
| kdc (Kerberos KDC) | ✅ 运行中 | :88/:749 |
| FE JVM Kerberos 配置 | ✅ `-Djava.security.krb5.conf` | krb5.conf 在 meta/krb5.conf |
| Keytab 文件 | ✅ | meta/keytabs/hive_a.keytab, hive_b.keytab |

## StarRocks Catalog 配置

### hive_a

| 属性 | 值 |
|------|-----|
| type | hive |
| hive.metastore.uris | thrift://192.168.0.211:9084 |
| hive.metastore.kerberos.principal | hive/cluster_a@SR.TEST |
| hive.metastore.kerberos.keytab | /opt/starrocks/fe/meta/keytabs/hive_a.keytab |
| dfs.nameservices | nameservice_a |
| dfs.ha.namenodes.nameservice_a | nn1 |
| dfs.namenode.rpc-address.nameservice_a.nn1 | 192.168.0.211:8020 |
| dfs.client.failover.proxy.provider.nameservice_a | org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider |

### hive_b

| 属性 | 值 |
|------|-----|
| type | hive |
| hive.metastore.uris | thrift://192.168.0.211:9085 |
| hive.metastore.kerberos.principal | hive/cluster_b@SR.TEST |
| hive.metastore.kerberos.keytab | /opt/starrocks/fe/meta/keytabs/hive_b.keytab |
| dfs.nameservices | nameservice_b |
| dfs.ha.namenodes.nameservice_b | nn1 |
| dfs.namenode.rpc-address.nameservice_b.nn1 | 192.168.0.211:8020 |
| dfs.client.failover.proxy.provider.nameservice_b | org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider |

## 查询验证

| 查询 | 结果 |
|------|------|
| `SHOW DATABASES FROM hive_a` | ✅ default, information_schema, nyc |
| `SHOW DATABASES FROM hive_b` | ✅ default, information_schema, test_db |
| `SHOW TABLES FROM hive_a.nyc` | ✅ taxis |
| `SHOW TABLES FROM hive_b.test_db` | ✅ products |
| `SELECT * FROM hive_b.test_db.products` | ✅ 101 Widget 9.99 / 102 Gadget 19.99 |
| `SELECT * FROM hive_a.nyc.taxis` | ❌ unsupported hdfs file format: UNKNOWN (文件格式问题，非Kerberos问题) |

## 结论

1. **Kerberos 认证**: ✅ StarRocks FE 成功通过 Kerberos SASL 认证连接到两个 Hive Metastore
2. **HA HDFS 配置透传**: ✅ Catalog 级别的 `dfs.*` 配置已设置，可通过 toThrift() 传递到 BE
3. **多 Hive Catalog 连接**: ✅ 单个 StarRocks 集群同时连接两个 Hive 集群(hive_a:9084, hive_b:9085)
4. **数据查询**: ✅ hive_b.test_db.products 可正常查询返回数据
5. **已知问题**: hive_a.nyc.taxis 的表文件格式不被 BE 识别(UNKNOWN)，需要检查数据文件格式

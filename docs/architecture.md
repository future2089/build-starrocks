# Architecture: Multi-Catalog Secure HA HDFS

## 问题

StarRocks 原生 Hive Catalog 不支持：
1. 每个 Catalog 独立的 HDFS HA 配置（nameservice, namenode addresses）
2. 每个 Catalog 独立的 Kerberos 认证凭据

导致无法同时连接两个不同 HDFS HA 名称服务的安全 Hive 集群。

## 解决方案

### 数据流

```
StarRocks FE
  │
  ├── HiveConnector (per catalog)
  │     │
  │     ├── HDFSCloudCredential ──→ hadoopConfiguration(Map<String,String>)
  │     │     │                         │
  │     │     │ applyToConfiguration()  │ inject all props into Configuration
  │     │     │ toThrift()              │ forward dfs.*/hadoop.* props to BE
  │     │     │ toFileStoreInfo()        │ (existing, puts into FileStoreInfo)
  │     │     │
  │     ├── HiveMetaClient
  │     │     │  krbPrincipal, krbKeytab (per catalog)
  │     │     │  callRPC() → doAsWithSwap() → UGI.doAs()
  │     │     │
  │     └── HadoopExt
  │             doAsWithSwap(principal, keytab, action)
  │               → loginUserFromKeytab()
  │               → UserGroupInformation.doAs()
  │
  └── BE
        receives dfs.*/hadoop.* properties via Thrift
        creates HDFS FileSystem with per-catalog config
```

### 修改点

| 文件 | 改动 |
|---|---|
| `HDFSCloudCredential.java` | `applyToConfiguration()` — 注入 hadoopConfiguration 到 Hadoop Configuration |
| | `toThrift()` — 将 HA/Kerberos 配置传递给 BE |
| `HadoopExt.java` | 新增 `doAsWithSwap(principal, keytab, action)` — per-catalog Kerberos UGI 切换 |
| `HiveMetaClient.java` | 新增 `krbPrincipal`/`krbKeytab` 字段；`callRPC()` 使用 `doAsWithSwap()` |

### 部署拓扑

```
┌──────────────────────────────────────────────────────────┐
│ 192.168.0.211 (openEuler 24.03)                         │
│                                                          │
│  ┌─────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐ │
│  │   KDC   │  │ Cluster A │  │ Cluster B │  │  SR    │ │
│  │ :88/749 │  │ HMS :9084 │  │ HMS :9085 │  │ :9030  │ │
│  │         │  │ krb=yes   │  │ krb=yes   │  │        │ │
│  │ KRB5    │  │ HA=ns_a   │  │ HA=ns_b   │  │        │ │
│  └─────────┘  └─────┬─────┘  └─────┬─────┘  └────────┘ │
│                      │              │                    │
│                      └──────┬───────┘                    │
│                             │                            │
│                    ┌────────▼────────┐                    │
│                    │     HDFS        │                    │
│                    │  NN :8020       │                    │
│                    │  (SIMPLE auth)  │                    │
│                    └─────────────────┘                    │
└──────────────────────────────────────────────────────────┘
```

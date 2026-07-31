# 架构

单个 StarRocks 集群同时连接多个**不同 Kerberos realm** 的安全 HA HDFS / Hive 集群。

## 能力缺口

社区版 StarRocks 3.3.17 缺三样东西：

1. **HDFS HA 配置无法 per-catalog 下发到 BE**
   `HDFSCloudCredential.toThrift()` 是空实现，catalog 里配的 `dfs.nameservices` 等
   到不了 BE。BE 只能读自己 `conf/` 下那份全局 `hdfs-site.xml`。
   （这个空实现在 4.0 依然存在。）

2. **BE 侧所有 catalog 共用一个 Kerberos 身份**
   `HadoopExt.getHDFSUGI()` 是空实现返回 null，导致 `doAs(null, ...)` 退化为
   JVM 全局 loginUser。多 realm 互斥。

3. **FE 侧访问 HMS 时元数据串行**
   凭据切换靠改全局状态，只能整段加锁。

## 数据流

```
                      ┌─────────────────────── FE ───────────────────────┐
                      │                                                  │
  CREATE CATALOG      │  HiveConnector (per catalog)                     │
  PROPERTIES (...)  ──┼─→ HDFSCloudConfigurationProvider                 │
                      │       │  接受 hadoop.security.krb5.principal 等   │
                      │       │  标准 Hadoop key 通过凭据校验             │
                      │       ▼                                          │
                      │   HDFSCloudCredential                            │
                      │       ├─ applyToConfiguration()                  │
                      │       │    注入 hadoopConfiguration 到 Configuration
                      │       └─ toThrift()                              │
                      │            过滤 dfs./hadoop./ipc./hive. 前缀 ─────┼──┐
                      │                                                  │  │
                      │   HiveMetaClient.callRPC()                       │  │
                      │       └─ HadoopExt.doAsWithSwap(p, k, krb5, act) │  │
                      │            ├─ canSkipKrb5Swap() ? 无锁快路径      │  │
                      │            │    getOrCreateKeytabUGI() → doAs    │  │
                      │            └─ 否则 legacy 串行路径（兼容）        │  │
                      │                       │                          │  │
                      └───────────────────────┼──────────────────────────┘  │
                                              │ SASL                        │ Thrift
                                              ▼                             ▼
                                      ┌──────────────┐            ┌─────── BE ────────┐
                                      │ Hive         │            │                   │
                                      │ Metastore    │            │ 定制 FileSystem   │
                                      │ (每集群一个) │            │  .createFileSystem│
                                      └──────────────┘            │     │             │
                                                                  │     ├ rewriteConfiguration
                                                                  │     ├ getHDFSUGI(conf)
                                                                  │     │   → 按 principal@@keytab
                                                                  │     │     缓存独立 UGI
                                                                  │     └ doAs(ugi, 建 FS)
                                                                  │           │         │
                                                                  └───────────┼─────────┘
                                                                              │ Kerberos RPC
                                                                              ▼
                                                                      ┌──────────────┐
                                                                      │ HA HDFS      │
                                                                      │ NN1/NN2 + DN │
                                                                      └──────────────┘
```

关键点：`doAs(ugi, ...)` 内创建的 DFSClient / RPC 代理**永久绑定该 UGI**。
后续所有 IO 自动带正确身份，无需在每次读写时重新切换。

原理详解见 `kerberos-isolation.md`。

## 改动清单

| 文件 | 层 | 改动 |
|---|---|---|
| `HadoopExt.java` | FE + BE | 实现 `getHDFSUGI()`：用 `loginUserFromKeytabAndReturnUGI` 建 per-catalog 独立 UGI，按 `principal@@keytab` 缓存，`checkTGTAndReloginFromKeytab()` 自动续期 |
| | | 抽出 `getOrCreateKeytabUGI()` 供 FE/BE 共用 |
| | | `doAsWithSwap()` 加 `canSkipKrb5Swap()` 无锁快路径，消除 HMS 元数据串行 |
| `HDFSCloudCredential.java` | FE | 实现 `toThrift()`（透传 `dfs./hadoop./ipc./hive.` 前缀）与 `applyToConfiguration()` |
| `HDFSCloudConfigurationProvider.java` | FE | 允许标准 Hadoop key 通过 FE 侧凭据校验 |
| `HiveMetaClient.java` | FE | 加 `krbPrincipal`/`krbKeytab`/`krb5ConfPath` 字段；`callRPC()` 与 client 创建都用 `doAsWithSwap()` 包裹 |

**BE 侧没有 C++ 改动。** 早期的 `hdfs_fs_cache.cpp` 补丁已证伪并归档，
见 `patches/obsolete/WHY_OBSOLETE.md`。

## 类加载

StarRocks 用自己的 `org/apache/hadoop/fs/FileSystem.class` 替换 Hadoop 原版，
打包在 `starrocks-hadoop-ext.jar` 里并置于 CLASSPATH **首位**。

FE 和 BE 各有一份**独立的** `starrocks-hadoop-ext.jar`：

```
/opt/starrocks/fe/lib/starrocks-hadoop-ext.jar              ← FE，HMS 认证
/opt/starrocks/be/lib/jni-packages/starrocks-hadoop-ext.jar ← BE，HDFS 认证
```

两者都会覆盖 `starrocks-fe.jar` 中的同名类。热部署时**必须两个都更新**。

## 部署拓扑

```
┌─ 192.168.0.211 (openEuler, x86) ───────────────────────────────┐
│                                                                │
│  ┌─ 容器 sr ──────────────┐    ┌─ 容器 hive_c ───────────────┐ │
│  │  FE  :9030 :8030       │    │  realm  EXAMPLE.COM         │ │
│  │  BE  :9060 :8040       │    │  KDC    :88                 │ │
│  │                        │    │  HMS    :9083  (SASL)       │ │
│  │  krb5/                 │    │  HS2    :10000 (KERBEROS)   │ │
│  │   ├ user_c.keytab      │    │  MySQL  :3306  (hive_c 库)  │ │
│  │   └ user_arm.keytab    │    │  ZK     :2181               │ │
│  └───────┬────────────────┘    │  HA HDFS  nameservice=hacluster
│          │                     │    NN1 :8020 active         │ │
│          │  catalog            │    NN2 :8022 standby        │ │
│          │  hive_hivec ───────→│    JN  :8485-8487           │ │
│          │                     │    DN  :9866                │ │
│          │                     │  ZKFC  nn1:8019 nn2:18023   │ │
│          │                     │  YARN  :8032 :8088          │ │
│          │                     └─────────────────────────────┘ │
└──────────┼─────────────────────────────────────────────────────┘
           │
           │  catalog hive_catalog
           │
┌──────────▼─ 192.168.0.181 (鲲鹏 920, ARM64) ───────────────────┐
│  ┌─ 容器 hive_arm ────────────────────────────────────────┐    │
│  │  realm  HIVE_ARM.TEST                                  │    │
│  │  KDC    :8888   kadmind :7490                          │    │
│  │  HMS    :9086  (SASL)                                  │    │
│  │  HS2    :10003 (KERBEROS)                              │    │
│  │  HDFS   fs.defaultFS = hdfs://arm-ha                   │    │
│  │    NN :8021 (web 50071)   DN :9866                     │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

两个集群 realm 不同、KDC 独立、无跨域信任。FE 与 BE 靠 per-catalog keytab
分别登录各自 KDC，互不干扰。

**注意 181 的 docker exec / docker cp 已损坏**（daemon 与 runc 版本不兼容）。
进容器要用：

```bash
nsenter -t $(docker inspect -f '{{.State.Pid}}' hive_arm) -m -u -i -n -p <cmd>
```

写容器内文件走宿主路径更可靠：
`/proc/$(docker inspect -f '{{.State.Pid}}' hive_arm)/root/<容器内路径>`

## 凭据布局

```
/opt/starrocks/krb5/
├── user_c.keytab      user_c@EXAMPLE.COM      (chmod 644)
└── user_arm.keytab    user_arm@HIVE_ARM.TEST  (chmod 644)

/etc/krb5.conf                    ← BE 用
/opt/starrocks/fe/meta/krb5.conf  ← FE 用（-Djava.security.krb5.conf 指向它）
```

两份 krb5.conf 内容一致，都包含双 realm 定义和 `[domain_realm]` 映射：

```ini
[domain_realm]
    hive-c    = EXAMPLE.COM
    .hive-c   = EXAMPLE.COM
    hacluster = EXAMPLE.COM
    arm-ha    = HIVE_ARM.TEST
```

nameservice 名也必须映射 —— HA 模式下客户端会拿它当 host 做 SASL 规范化。

**系统内不需要任何 ticket cache。** 所有身份都由 per-catalog keytab 现登录并自动续期。

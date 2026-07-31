# Build StarRocks — 单集群并发访问多个异构安全 HA HDFS / Hive 集群

> **最后更新：2026-07-31** ｜ 基线版本：**StarRocks 3.3.17 (commit 3eac4a9)**
>
> 本仓库对 StarRocks 3.3.17 打补丁并编译，让**一个 StarRocks 集群同时安全连接多个不同 Kerberos realm 的 Hive 集群**，每个 catalog 用各自独立的 principal/keytab，互不串扰。

---

## 1. 能力与定位

社区版 StarRocks 3.3.17 缺三样东西，本项目一一补齐：

| # | 能力缺口                                                                                                                       | 本项目的解                                                                         |
| - | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1 | **HDFS HA 配置无法 per-catalog 下发到 BE** —— `HDFSCloudCredential.toThrift()` 是空实现，catalog 里配的 `dfs.nameservices` 等传不到 BE        | 实现 `toThrift()` 透传 `dfs./hadoop./ipc./hive.` 前缀属性                             |
| 2 | **BE 侧所有 catalog 共用一个 Kerberos 身份** —— `HadoopExt.getHDFSUGI()` 空实现返回 null，导致 `doAs(null)` 退化为 JVM 全局 loginUser，多 realm 互斥 | 实现 `getHDFSUGI()`，用 `loginUserFromKeytabAndReturnUGI` 为每个 catalog 建独立 UGI 并缓存 |
| 3 | **FE 侧访问 HMS 时元数据串行** —— 凭据切换靠改全局状态，只能整段加锁                                                                                 | `doAsWithSwap()` 加 `canSkipKrb5Swap()` 无锁快路径，各 catalog 并行访问                   |

**达成效果（2026-07-31 验证）：** 单个 StarRocks 集群同时访问两个**无跨域信任、KDC 完全独立**的安全 Hive 集群（`EXAMPLE.COM` 与 `HIVE_ARM.TEST`），在**系统内不存在任何 Kerberos ticket cache、也没有任何 kinit 续期守护进程**的条件下稳定出数，跨集群 JOIN / UNION 正常。

> 关键认知：**BE 侧没有任何 C++ 改动**。早期 `hdfs_fs_cache.cpp` 的 per-catalog KRB5CCNAME 补丁已证伪并归档（见第 5 节、[`patches/obsolete/WHY_OBSOLETE.md`](../patches/obsolete/WHY_OBSOLETE.md)）。真正的解全在 Java 层。

---

## 2. 架构

```
                      ┌─────────────────────── FE ───────────────────────┐
  CREATE CATALOG      │  HiveConnector (per catalog)                     │
  PROPERTIES (...)  ──┼─→ HDFSCloudCredential                           │
                      │       ├─ applyToConfiguration() 注入 hadoopConfig │
                      │       └─ toThrift() 透传 dfs./hadoop./ipc./hive. ─┼──┐
                      │   HiveMetaClient.callRPC()                       │  │
                      │       └─ HadoopExt.doAsWithSwap(p,k,krb5,act)     │  │
                      │            ├─ canSkipKrb5Swap()? 无锁快路径       │  │
                      │            │     getOrCreateKeytabUGI()→doAs     │  │
                      │            └─ 否则 legacy 串行路径（兼容）        │  │
                      └───────────────────────┼──────────────────────────┘  │
                                              │ SASL                        │ Thrift
                                              ▼                             ▼
                                      ┌──────────────┐            ┌─────── BE ────────┐
                                      │ Hive         │            │ 定制 FileSystem    │
                                      │ Metastore    │            │  .createFileSystem│
                                      │ (每集群一个) │            │    │ rewriteConfig  │
                                      └──────────────┘            │    ├ getHDFSUGI(c) │
                                                                  │    │  → 按 principal@@keytab
                                                                  │    │    缓存独立 UGI   │
                                                                  │    └ doAs(ugi, 建 FS) │
                                                                  └───────────┼─────────┘
                                                                              │ Kerberos RPC
                                                                              ▼
                                                                      ┌──────────────┐
                                                                      │ HA HDFS      │
                                                                      │ NN1/NN2 + DN │
                                                                      └──────────────┘
```

**核心要点**：`doAs(ugi, ...)` 内创建的 DFSClient / RPC 代理**永久绑定该 UGI**，后续所有 IO 自动带正确身份，无需每次读写重新切换。

**类加载（极易踩坑）**：StarRocks 用自己的 `org/apache/hadoop/fs/FileSystem.class` 替换 Hadoop 原版，打包在 `starrocks-hadoop-ext.jar` 里并置于 CLASSPATH **首位**。**FE 和 BE 各有一份独立的 jar**：

```
/opt/starrocks/fe/lib/starrocks-hadoop-ext.jar              ← FE，HMS 认证
/opt/starrocks/be/lib/jni-packages/starrocks-hadoop-ext.jar ← BE，HDFS 认证
```

两者都会覆盖 `starrocks-fe.jar` 中的同名类。热部署时**必须两个都更新**，否则会出现"HDFS 隔离好了但 HMS 还串行"的半生效状态。

> 数据流、改动清单、类加载、凭据布局的完整说明见 [`docs/architecture.md`](docs/architecture.md)；per-catalog 隔离的核心原理深挖见 [`docs/kerberos-isolation.md`](docs/kerberos-isolation.md)。

---

## 3. 环境拓扑（三方真实部署，截至 2026-07-31）

```
┌─ 192.168.0.211 (openEuler, x86) ───────────────────────────────┐
│  ┌─ 容器 sr ──────────────┐    ┌─ 容器 hive_c ───────────────┐ │
│  │  FE  :9030 :8030       │    │  realm  EXAMPLE.COM         │ │
│  │  BE  :9060 :8040       │    │  KDC    :88                 │ │
│  │  krb5/                 │    │  HMS    :9083  (SASL)       │ │
│  │   ├ user_c.keytab      │    │  HS2    :10000 (KERBEROS)   │ │
│  │   └ user_arm.keytab    │    │  MySQL  :3306  (hive_c 库)  │ │
│  └───────┬────────────────┘    │  ZK     :2181               │ │
│          │                     │  HA HDFS  nameservice=hacluster
│          │  catalog            │    NN1 :8020 active         │ │
│          │  hive_hivec ───────→│    NN2 :8022 standby        │ │
│          │                     │    JN  :8485-8487  DN :9866 │ │
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

两个集群 **realm 不同、KDC 独立、无跨域信任**。FE 与 BE 靠 per-catalog keytab 分别登录各自 KDC，互不干扰。

**凭据布局**：

```
/opt/starrocks/krb5/
├── user_c.keytab      user_c@EXAMPLE.COM      (chmod 644, BE 读)
└── user_arm.keytab    user_arm@HIVE_ARM.TEST  (chmod 644, BE 读)

/opt/starrocks/fe/meta/
├── krb5.conf          ← FE 用（-Djava.security.krb5.conf 指向它，含双 realm + domain_realm）
├── user_c.keytab      user_c@EXAMPLE.COM      (FE 读，HMS 客户端身份)
└── user_arm.keytab    user_arm@HIVE_ARM.TEST  (FE 读，HMS 客户端身份)
/etc/krb5.conf         ← BE 用，内容与 FE 那份一致
```

> ⚠️ **181 的 `docker exec` / `docker cp` 已损坏**（daemon 与 runc 版本不兼容）。进容器要用：
>
> ```bash
> nsenter -t $(docker inspect -f '{{.State.Pid}}' hive_arm) -m -u -i -n -p <cmd>
> ```
>
> 写文件走宿主路径更可靠：`/proc/$(docker inspect -f '{{.State.Pid}}' hive_arm)/root/<容器内路径>`

---

## 4. 核心原理（为什么社区版多 realm 一定串扰）

给 StarRocks 建两个 Hive catalog，分别指向两个安全集群：

- `hive_hivec` → `hive_c`，realm `EXAMPLE.COM`，客户端身份 `user_c`
- `hive_catalog` → ARM 集群，realm `HIVE_ARM.TEST`，客户端身份 `user_arm`

**症状**：同一时刻只有一个能查。另一个必报 `KrbApErrException: Fail to create credential. (63) - No service creds`。而且哪个能通取决于系统默认 ticket cache（`/tmp/krb5cc_0`）里当前是谁 —— `kinit` 成 `user_arm` 则 `hive_catalog` 通、`hive_hivec` 挂；换成 `user_c` 则反过来。这种**完美对称性**说明两个 catalog 根本没有各自的身份，在共用同一个全局凭据。

### 根因

StarRocks 用自己的 `FileSystem` 类替换 Hadoop 原版（打包进 `starrocks-hadoop-ext.jar`，排在 BE CLASSPATH 最前）。反编译 `createFileSystem(URI, Configuration)` 有三个钩子：

```java
HadoopExt.getInstance().rewriteConfiguration(conf);
UserGroupInformation ugi = HadoopExt.getInstance().getHDFSUGI(conf);
return HadoopExt.getInstance().doAs(ugi, () -> /* 真正创建 FileSystem */);
```

设计意图是留口子让每个 catalog 用自己的 UGI 建 FileSystem。**但社区版 `getHDFSUGI()` 是空实现，直接 return null。** `doAs(null, ...)` 退化成"用 JVM 全局 loginUser 执行" —— 全局 loginUser 全进程只有一个，同一时刻只能持有一个 realm 的凭据。于是所有 catalog 挤在同一个身份上。

### 解法：选对 API 比写多少代码都重要

| API                                     | 行为                      | 能否用于多 realm          |
| --------------------------------------- | ----------------------- | -------------------- |
| `loginUserFromKeytab(p, k)`             | **改写 JVM 全局 loginUser** | 不能。第二次调用顶掉第一次        |
| `loginUserFromKeytabAndReturnUGI(p, k)` | 返回**独立的 UGI 对象**，不碰全局状态 | **可以**。多个 realm 各持一份 |

```java
public UserGroupInformation getHDFSUGI(Configuration conf) {
    String principal = firstNonEmpty(conf, PRINCIPAL_KEYS);
    String keytab    = firstNonEmpty(conf, KEYTAB_KEYS);
    if (principal == null || keytab == null) return null;   // 保持原行为

    String cacheKey = principal + "@@" + keytab;
    UserGroupInformation ugi = HDFS_UGI_CACHE.get(cacheKey);
    if (ugi == null) {
        synchronized (HDFS_UGI_CACHE) {
            ugi = HDFS_UGI_CACHE.get(cacheKey);
            if (ugi == null) {
                ensureKerberosEnabled();
                ugi = UserGroupInformation.loginUserFromKeytabAndReturnUGI(principal, keytab);
                HDFS_UGI_CACHE.put(cacheKey, ugi);
            }
        }
    } else {
        ugi.checkTGTAndReloginFromKeytab();   // 自动续期，无需外部 kinit 守护
    }
    return ugi;
}
```

三个设计点：

- **按 `principal@@keytab` 缓存** —— 同一 catalog 复用同一 UGI，避免反复登录 KDC；
- **`checkTGTAndReloginFromKeytab()`** —— TGT 快过期时自动续，这就是"系统内无任何 ticket cache 也能长期稳定运行"的原因；
- **登录失败返回 null** —— 退回原行为，不会让原本能用的场景变坏。

### FE 侧：同样的问题，稍有不同

FE 访问 HMS 走 `HiveMetaClient.callRPC()`，用 `HadoopExt.doAsWithSwap(principal, keytab, krb5ConfPath, action)` 包裹。早期实现整段 `synchronized(UserGroupInformation.class)` 串行执行 —— 能跑但所有 catalog 的元数据访问全部串行。

优化加一条无锁快路径 `canSkipKrb5Swap()`：实际部署的 `HiveMetaClient` 调的是 4 参数版，`krb5ConfPath` 永远非 null，所以最初写的 `if (krb5ConfPath == null)` 快路径永远进不去（部署后日志里只有 HDFS UGI、没有 HMS UGI，看起来像没生效）。进一步核对发现 FE 启动参数 `-Djava.security.krb5.conf` 与 catalog 里配的 `krb5.conf` **指向同一文件且已含全部 realm**，那次 swap 纯属空操作却付出全量串行代价。条件放宽为 `canSkipKrb5Swap()`（比对路径是否同一文件），满足时走 `getOrCreateKeytabUGI()`（与 BE 共用的独立 UGI 缓存），无全局锁、不改全局 loginUser。

**前提**：单个 krb5.conf 必须包含所有 realm + 对应的 `[domain_realm]` host 映射（本来也是多集群推荐配置）。

### 两条走不通的路（已证伪）

- **C++ 层 `setenv("KRB5CCNAME")`**：BE 通过 libhdfs 走 JNI，真正建连的是 JVM 里的 Java 代码，而 `System.getenv()` 读的是 **JVM 启动时的环境快照** —— 运行期再 `setenv` 对 JVM 完全不可见。详见 [`patches/obsolete/WHY_OBSOLETE.md`](../patches/obsolete/WHY_OBSOLETE.md)。
- **BE 启动前 `kinit`**：单集群没问题，多 realm 天然不行 —— 一个 ticket cache 只能是一个身份。这正是问题本身。

---

## 5. 补丁清单

源码改动位于 [`patches/`](patches/)，对 StarRocks 3.3.17 走**全量编译**路径时使用。

| 文件                                                           | 层        | 作用                                                                        | 必需性                                  |
| ------------------------------------------------------------ | -------- | ------------------------------------------------------------------------- | ------------------------------------ |
| `HadoopExt.java`                                             | FE + BE  | **per-catalog 独立 UGI**：BE 实现 `getHDFSUGI()`，FE 给 `doAsWithSwap()` 加无锁快路径  | **★ 核心，缺它整套方案不成立**                   |
| `starrocks-fe.patch` → `HiveMetaClient.java`                 | FE       | 读 catalog 的 `hive.metastore.kerberos.*`，用 `doAsWithSwap()` 包裹 HMS RPC     | 必需                                   |
| `starrocks-fe.patch` → `HDFSCloudCredential.java`            | FE       | 实现 `toThrift()`（`dfs./hadoop./ipc./hive.` 前缀透传）与 `applyToConfiguration()` | 必需（HDFS HA 透传）                       |
| `starrocks-fe.patch` → `HDFSCloudConfigurationProvider.java` | FE       | 允许标准 Hadoop key 通过 FE 侧凭据校验                                               | 必需                                   |
| `obsolete/starrocks-be.patch`                                | BE (C++) | ~~per-catalog KRB5CCNAME~~                                                | **已废弃**，见 `obsolete/WHY_OBSOLETE.md` |

**没有 BE C++ 补丁。** 早期 `hdfs_fs_cache.cpp` 的 `setenv("KRB5CCNAME")` 方案已被三条证据证伪：`setenv` 对 JVM 不可见 / `catalog_id` 从未赋值 / 线上二进制未含它却全通。真正的解全在 Java 层。

### 必须知道的坑：`HadoopExt.java` 不在 `.patch` 文件里

它是改动量最大的文件，`git apply` 打不进去，必须由 `patches/apply_patches.sh` 额外 `cp` 到**两个位置**：

```
fe/fe-core/src/main/java/com/starrocks/connector/hadoop/HadoopExt.java
    → 编译进 starrocks-fe.jar，FE 用（HMS 认证）

java-extensions/hadoop-ext/src/main/java/com/starrocks/connector/hadoop/HadoopExt.java
    → 编译进 starrocks-hadoop-ext.jar，BE 用（HDFS 认证）
```

两份内容必须**完全一致**。只 `git apply` 不跑脚本，会得到一个能编译、能启动、单集群也能查，但**多 realm 一定串扰**的版本 —— 而且不报错，只是第二个 catalog 查不出来。`apply_patches.sh` 末尾会校验两份文件里都有 `getHDFSUGI` / `getOrCreateKeytabUGI` / `loginUserFromKeytabAndReturnUGI`。

详细补丁说明见 [`patches/README.md`](patches/README.md)。

---

## 6. 两条上手路径

### 路径 A：全量编译（从源码构建新版本）

适用：首次部署、需要重新编译、或要长期维护 fork。

```bash
cd /data/starrocks-build/starrocks-3.3.17
bash /path/to/patches/apply_patches.sh

# FE（十几分钟）
cd fe && mvn package -DskipTests -Dcheckstyle.skip=true

# BE（cc1plus 约 4GB/进程，先加 swap，别开满核）
./build.sh --be -j 2
```

BE 编译易 OOM（内存不足先加 swap）：

```bash
dd if=/dev/zero of=/data/swapfile bs=1M count=16384
chmod 600 /data/swapfile && mkswap /data/swapfile && swapon /data/swapfile
```

### 路径 B：热部署（已有集群，免重编译，约 5 分钟）

适用：已经跑着 3.3.17、只是想让改动立刻生效。只改 Java 类（BE C++ 二进制改不了 —— 好在本方案不需要动 C++）。脚本位于 [`deploy/`](deploy/)：

```bash
# 1. 上传源码和脚本到容器
scp patches/HadoopExt.java deploy/*.sh root@192.168.0.211:/tmp/
ssh root@192.168.0.211 'docker exec sr mkdir -p /tmp/hp && \
  for f in HadoopExt.java hotpatch_hadoop_ext.sh restart_fe.sh restart_be.sh; do \
    docker cp /tmp/$f sr:/tmp/hp/; done'

# 2. 热部署 FE + BE 两个 jar（脚本默认两个都打，自动备份 .orig / .bak_时间戳）
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/hotpatch_hadoop_ext.sh'

# 3. 重启（用 deploy 脚本，处理了容器 PID 1 不 reap 导致的 pid 残留问题）
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/restart_fe.sh'
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/restart_be.sh'

# 4. 验证
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/verify_multi_kerberos.sh'
```

> 远程复杂命令**不要**直接嵌在 `ssh "docker exec ... '...'"` 里（多层引号嵌套会吞输出）。固定做法：本地写脚本 → `scp` → `docker cp` → `docker exec bash 脚本`。非交互 `docker exec -i` 不加载登录 profile，脚本内要显式 `export JAVA_HOME=/usr/lib/jvm/java-11; export PATH=$JAVA_HOME/bin:$PATH`。

`deploy/` 脚本与路径分工的完整说明见 [`deploy/README.md`](deploy/README.md)。

---

## 7. Catalog 配置规范

已验证可用的完整模板见 [`deploy/multi_kerberos_catalogs.sql`](deploy/multi_kerberos_catalogs.sql)。四个必须遵守的规范：

### 7.1 HDFS 凭据必须用 `hadoop.` 前缀

FE 的 `HDFSCloudCredential.toThrift()` 只透传四类前缀到 BE：`dfs.` / `hadoop.` / `ipc.` / `hive.`。**写成 `hdfs.kerberos.principal` 到不了 BE**，BE 会退回全局 ccache 导致多 realm 互斥。

```sql
"hadoop.security.authentication" = "kerberos",
"hadoop.kerberos.principal"      = "user_c@EXAMPLE.COM",
"hadoop.kerberos.keytab"         = "/opt/starrocks/krb5/user_c.keytab"
```

（`getHDFSUGI()` 里 `PRINCIPAL_KEYS`/`KEYTAB_KEYS` 各接受三种写法作兼容，但只有 `hadoop.` 开头的能真正传到 BE。）

### 7.2 krb5.conf 必须有 `[domain_realm]` 映射

Hive SASL 用 hostbased 规范化，`hive/hive-c@EXAMPLE.COM` 会被拆成 `hive@hive-c`（**realm 被丢掉**），再由 `[domain_realm]` 反查 host 属于哪个 realm。缺少 `hive-c → EXAMPLE.COM` 映射会回落到 `default_realm`，跨域直接失败。

```ini
[domain_realm]
    hive-c  = EXAMPLE.COM
    .hive-c = EXAMPLE.COM
    hacluster = EXAMPLE.COM
    arm-ha  = HIVE_ARM.TEST
```

**HA nameservice 名（`hacluster` / `arm-ha`）也要映射** —— HA 模式下客户端会拿它当 host 做 SASL 规范化。

### 7.3 `hadoop.security.auth_to_local` 要含所有 realm 的 RULE

否则报 `KerberosName$NoMatchingRule`。配在 BE/FE 的 `core-site.xml` 里，每个 realm 都要有 RULE。

### 7.4 keytab 路径与权限

- BE 读的那份放在 `/opt/starrocks/krb5/`，`chmod 644`，路径在 BE 进程里可读；
- FE 读的那份放在 `/opt/starrocks/fe/meta/`，`chmod 644`；
- `hive.metastore.kerberos.keytab` 指向 FE 那份，`hadoop.kerberos.keytab` 指向 BE 那份。

---

## 8. 验证方法（三层验证法）

排障经验：有 ticket cache 时，即使代码没生效也可能"碰巧"查通。所以验证必须分三层，**只有第三层通过才算数**。

### 第 1 层：有默认 ccache 时能查

基础功能，**不足以证明隔离生效** —— 可能只是命中了全局身份。

### 第 2 层：对称性实验

把 `/tmp/krb5cc_0` 换成另一个身份，观察哪个 catalog 通：

| `/tmp/krb5cc_0` 里的身份     | `hive_hivec`       | `hive_catalog`     |
| ------------------------ | ------------------ | ------------------ |
| `user_arm@HIVE_ARM.TEST` | `No service creds` | 出数                 |
| `user_c@EXAMPLE.COM`     | 出数                 | `No service creds` |

修复后再做这个实验，两个 catalog 应都不受 ccache 内容影响。

### 第 3 层：无 ccache 裸环境（决定性）

```bash
pkill -f renew.sh                       # 杀掉所有 kinit 续期守护
rm -f /tmp/krb5cc_* /opt/starrocks/krb5/cc_*
klist                                   # 应输出 No credentials cache found
# 重启 FE + BE
```

在此状态下全部查询仍成功 → 证明走的是 per-catalog keytab 独立登录。

### 日志判读

每个 catalog 首次访问时各打一条（按 `principal@@keytab` 缓存，不重复登录）：

```
be.out: [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=user_c@EXAMPLE.COM
be.out: [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=user_arm@HIVE_ARM.TEST
fe.out: [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=user_c@EXAMPLE.COM
fe.out: [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=user_arm@HIVE_ARM.TEST
```

### 用 jstack 确认并发真的不串行

压测**进行中**抓 FE 线程栈，直接看有没有线程卡在 UGI 全局锁上：

```bash
jstack <fe_pid> > /tmp/st.txt
grep -c "waiting to lock.*UserGroupInformation" /tmp/st.txt   # 应为 0
grep -c "java.lang.Thread.State: BLOCKED" /tmp/st.txt         # 应为 0
```

### 打标记法排除历史日志干扰

fe.out/be.out 动辄几万行，旧 jar 时期的报错一直躺在里面。判断增量报错：

```bash
MARK="=== PROBE $(date +%s) ==="
echo "$MARK" >> fe.out
mysql -e "REFRESH EXTERNAL TABLE hive_catalog.default.test_tbl; SELECT ..."
sed -n "/$MARK/,\$p" fe.out | grep -i "error\|exception"   # 无输出即真没问题
```

**必须 `REFRESH EXTERNAL TABLE`**，否则走元数据缓存，根本不会访问 HMS/HDFS，日志什么都不会新增。

端到端验证脚本见 [`deploy/verify_multi_kerberos.sh`](deploy/verify_multi_kerberos.sh)。

完整验证记录见 [`docs/verification_results.md`](docs/verification_results.md)；症状→根因速查见 [`docs/troubleshooting.md`](docs/troubleshooting.md)。

---

## 9. 常见问题（Top 5）

| 症状                                                   | 根因                                                                                 | 处置                                                                                                                                           |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `Fail to create credential. (63) - No service creds` | ① per-catalog UGI 没生效（最常见，呈"完美对称性"）② catalog 属性用错前缀 ③ krb5.conf 缺 `[domain_realm]` | `grep "per-catalog" be.out/fe.out` 看日志；`javap` 确认 jar 含 `loginUserFromKeytabAndReturnUGI`；确认 FE+BE 两份 jar 都打了；改用 `hadoop.` 前缀；补 domain_realm |
| `KerberosName$NoMatchingRule`                        | `core-site.xml` 的 `auth_to_local` 没覆盖该 realm                                       | 每个 realm 都加 RULE，重启                                                                                                                          |
| 只更新了一个 jar，表现"半生效"                                   | FE/BE 各有一份独立 `starrocks-hadoop-ext.jar`                                            | 用 `deploy/hotpatch_hadoop_ext.sh`，默认两个都打                                                                                                     |
| `start_be.sh`/`start_fe.sh` 拒绝启动                     | `sr` 容器 PID 1 不 reap，残留 `*.pid` 让脚本以为服务在跑                                          | 用 `deploy/restart_be.sh`/`restart_fe.sh`（精确 kill → 删 pid → 重启）                                                                               |
| 多 realm 仍串扰，但编译启动都正常                                 | `HadoopExt.java` 不在 `.patch` 里，`git apply` 打不进去                                    | 必须跑 `patches/apply_patches.sh` 额外 cp 到两个源码位置                                                                                                 |

更多症状（SIMPLE 报错、KDC 侧 `kvno` 验证、DN 注册、count(*) 返回 0、编译 OOM 等）见 [`docs/troubleshooting.md`](docs/troubleshooting.md)。

---

## 10. 已验证结果（2026-07-31）

**结论**：单个 StarRocks 集群同时访问两个不同 realm 的安全 Hive 集群，功能与并发均已打通，且**系统内不存在任何 Kerberos ticket cache、也没有任何 kinit 续期守护进程**。

### 功能验证（无 ccache 条件下）

| 项目                                              | 结果                                                  |
| ----------------------------------------------- | --------------------------------------------------- |
| `klist`                                         | `No credentials cache found` ✓                      |
| `/tmp/krb5cc_*` / `/opt/starrocks/krb5/cc_*`    | 不存在 ✓                                               |
| `SHOW CATALOGS`                                 | `default_catalog` / `hive_catalog` / `hive_hivec` ✓ |
| `SELECT ... FROM hive_hivec.demo.users`         | **5 行** ✓                                           |
| `SELECT ... FROM hive_catalog.default.test_tbl` | **2 行** ✓                                           |
| **跨集群 JOIN**                                    | **5 行**（carol/alice/dave × arm_id 1,2）✓             |
| 跨集群 UNION ALL                                   | `hive_c=5`、`arm=2` ✓                                |
| BE 重启后复测                                        | 全部保持 ✓（非偶发）                                         |

### 并发验证（FE `doAsWithSwap` 去串行后实测）

| 项目                                   | 结果         |
| ------------------------------------ | ---------- |
| 96 次并发元数据调用（16 并发 × 3 轮 × 2 catalog） | **3.34s**  |
| 8 并发跨集群 UNION                        | **0.147s** |
| 压测中等待 UGI 全局锁的线程                     | **0**      |
| 压测中 BLOCKED 线程                       | **0**      |
| 3 轮交替查询稳定性                           | 均 5/2，无抖动  |

### 早期验证（2026-07-16，已销毁环境）

第一阶段在 `cluster_a`/`cluster_b`（realm `SR.TEST`）验证：Kerberos HMS 认证、HDFS Kerberos 认证、跨 Catalog 元数据访问、HDFS HA 透传均通过。**但当时隔离靠 BE 启动前 `kinit` + `KRB5CCNAME`，本质仍是单一全局身份**，两个 catalog 恰好用同一 realm 才能同时工作。真正的跨 realm 场景直到 07-31 才解决。

### 已知限制

- `test_dml` 表（疑 Hive ACID 表）`SHOW TABLES` 可见，但 `DESC`/`SELECT` 报表不存在；
- Hive `count(*)` 默认读 metastore 统计信息，stats 过期时返回 0，需 `set hive.compute.query.using.stats=false` 或 `ANALYZE TABLE`；
- 补丁只在 3.3.x 上验证过，3.4+ 需 re-base（见第 11 节）。

完整验证过程与日志证据见 [`docs/verification_results.md`](docs/verification_results.md)。

---

## 11. 版本迁移

**只有停留在 3.3.x 才能 `git apply` 干净应用。** 升级到 3.4/3.5/4.0 时 `HiveMetaClient`（HMS 连接池）和 BE `FSOptions` 都已重构，两个锚点必须手动 re-base，且 3.4/3.5/4.0 成本几乎相同（重构都在 3.4 完成）。

| 升级目标                  | 补丁工作量  | 说明                                                    |
| --------------------- | ------ | ----------------------------------------------------- |
| 维持 3.3.x              | ~0.5 天 | 补丁近乎原样 apply                                          |
| 3.4.x / 3.5.x / 4.0.x | ~3–5 天 | 需手动 re-base `HiveMetaClient` 与 BE `hdfs_fs_cache.cpp` |

两个关键事实：

1. **`HDFSCloudCredential.toThrift()` 在 4.0 仍是空实现** —— 官方至今未原生支持 `dfs.*` 透传，本补丁仍有价值，但 BE 消费端已换 `THdfsProperties` 载体，需两端对齐；
2. **BE 侧 kerberos 身份（keytab/principal/KRB5CCNAME）在官方代码中完全不存在** —— 必须整段 re-port。

建议：若目标是新版上保留该特性，直接选 **3.5.x 或 4.0.x**（成本相同），不要为省补丁卡在 3.3.x。完整评估见 [`docs/patch_migration_assessment.md`](docs/patch_migration_assessment.md)。

---

## 12. 目录索引

```
build-starrocks/
├── README.md                       ← 你正在看的（入口文档）
├── patches/                       ← 源码补丁（全量编译路径）
│   ├── apply_patches.sh           ★ 必须跑：git apply + 额外 cp HadoopExt.java 到两处
│   ├── HadoopExt.java             ★ 核心：per-catalog 独立 UGI（不在 .patch 内）
│   ├── HDFSCloudCredential.java   ★ toThrift/applyToConfiguration 实现
│   ├── HiveMetaClient.java        ★ 读 per-catalog kerberos 凭据，doAsWithSwap 包裹
│   ├── starrocks-fe.patch         ← 上述三改动的 git diff
│   ├── obsolete/
│   │   ├── starrocks-be.patch     ← 已证伪的 C++ KRB5CCNAME 补丁
│   │   └── WHY_OBSOLETE.md        ← 三条证伪依据
│   └── README.md                  ← 补丁清单 + HadoopExt.java 不在 patch 内的坑
├── deploy/                        ← 运行期脚本（热部署路径，免重编译）
│   ├── hotpatch_hadoop_ext.sh     ★ 编译 HadoopExt.java 写回 FE+BE 两份 jar（自动备份）
│   ├── restart_fe.sh / restart_be.sh   ★ 处理容器 pid 残留的标准重启
│   ├── verify_multi_kerberos.sh   ★ 端到端验证（含无 ccache 检查）
│   ├── multi_kerberos_catalogs.sql    ★ 已验证的 catalog 定义模板
│   └── README.md                  ← patches vs deploy 分工 + 典型流程
├── docs/                          ← 深度文档
│   ├── architecture.md            ← 能力缺口 / 数据流 / 改动清单 / 类加载 / 拓扑 / 凭据布局
│   ├── kerberos-isolation.md      ← per-catalog 隔离原理深挖 + 两条死路
│   ├── troubleshooting.md         ← 症状→根因速查表
│   ├── verification_results.md    ← 三层验证 / 功能 / 并发 / 历史排除法
│   └── patch_migration_assessment.md ← 3.4/3.5/4.0 迁移成本评估
├── env/                           ← 环境配置留档
│   ├── configs/                   ← 各集群 krb5.conf / core-site / hdfs-site 等
│   ├── arm/                       ← ARM 侧 hive_arm 容器配置（含真实生效的 yarn/mapred 修复）
│   └── README.md
├── scripts/legacy/                ← 已归档的一次性/调试脚本（按场景分类，勿再依赖）
└── tmp/                           ← 临时排障产物（按用户要求保留，未清理）
```

---

### 快速开始清单

1. 读 [`docs/kerberos-isolation.md`](docs/kerberos-isolation.md) 搞懂原理；
2. 选路径 A（[`patches/`](patches/) 全量编译）或路径 B（[`deploy/`](deploy/) 热部署）；
3. 按第 7 节规范写 catalog（模板 [`deploy/multi_kerberos_catalogs.sql`](deploy/multi_kerberos_catalogs.sql)）；
4. 按第 8 节**三层验证法**确认真的隔离生效（重点：无 ccache 裸环境）；
5. 出问题先查 [`docs/troubleshooting.md`](docs/troubleshooting.md)。

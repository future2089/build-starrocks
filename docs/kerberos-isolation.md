# Per-catalog Kerberos 隔离原理

本文解释：为什么社区版 StarRocks 无法同时连接两个不同 Kerberos realm 的 Hive 集群，
以及本项目怎么解决的。

## 问题

给 StarRocks 建两个 Hive catalog，分别指向两个安全集群：

- `hive_hivec` → `hive_c`，realm `EXAMPLE.COM`，客户端身份 `user_c`
- `hive_catalog` → ARM 集群，realm `HIVE_ARM.TEST`，客户端身份 `user_arm`

现象：**同一时刻只有一个能查**。另一个必定报

```
KrbApErrException: Fail to create credential. (63) - No service creds
```

而且哪个能通取决于系统默认 ticket cache（`/tmp/krb5cc_0`）里当前是谁。
`kinit` 成 `user_arm` 则 `hive_catalog` 通、`hive_hivec` 挂；换成 `user_c` 则反过来。

这个**完美的对称性**是关键线索 —— 说明两个 catalog 根本没有各自的身份，
它们在共用同一个全局凭据。

## 根因

StarRocks 做了一件不太常见的事：**用自己的 `FileSystem` 类替换 Hadoop 原版**。

`org/apache/hadoop/fs/FileSystem.class` 被打包进 `starrocks-hadoop-ext.jar`，
而这个 jar 排在 BE CLASSPATH **最前面**，于是覆盖了 `hadoop-common-3.4.1.jar`
里的同名类。

反编译 `createFileSystem(URI, Configuration)` 能看到三个钩子：

```java
HadoopExt.getInstance().rewriteConfiguration(conf);
UserGroupInformation ugi = HadoopExt.getInstance().getHDFSUGI(conf);
return HadoopExt.getInstance().doAs(ugi, () -> /* 真正创建 FileSystem */);
```

设计意图很清楚：留一个口子，让每个 catalog 用自己的 UGI 去建 FileSystem。

但社区版的 `getHDFSUGI()` 是**空实现，直接 return null**。

`doAs(null, ...)` 退化成"用 JVM 全局 loginUser 执行" —— 而全局 loginUser 全进程
只有一个，同一时刻只能持有一个 realm 的凭据。于是所有 catalog 挤在同一个身份上。

## 解法

实现 `getHDFSUGI()`，为每个 catalog 建立**独立 UGI**。

关键在选对 API：

| API | 行为 | 能否用于多 realm |
|---|---|---|
| `loginUserFromKeytab(p, k)` | **改写 JVM 全局 loginUser** | 不能。第二次调用会顶掉第一次 |
| `loginUserFromKeytabAndReturnUGI(p, k)` | 返回一个**独立的 UGI 对象**，不碰全局状态 | **可以**。多个 realm 各持一份 |

两个方法名字只差后半截，行为天差地别。整个方案成立与否就在这一行。

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
        ugi.checkTGTAndReloginFromKeytab();   // 自动续期
    }
    return ugi;
}
```

三个设计点：

- **按 `principal@@keytab` 缓存**。同一 catalog 的所有 FileSystem 复用一个 UGI，
  避免反复登录 KDC。
- **`checkTGTAndReloginFromKeytab()`**。TGT 快过期时自动续，
  不需要外部 `kinit` 守护进程。这是能在"系统内无任何 ticket cache"条件下
  长期稳定运行的原因。
- **登录失败返回 null**。退回原行为（全局 UGI），不会让原本能用的场景变坏。

`doAs(ugi, ...)` 内创建的 DFSClient 和 RPC 代理会**永久绑定这个 UGI**，
后续所有读写自动带对的身份，不需要在每次 IO 时再做什么。

## FE 侧：同样的问题，稍有不同

FE 访问 Hive Metastore 走 `HiveMetaClient.callRPC()`，
它用 `HadoopExt.doAsWithSwap(principal, keytab, krb5ConfPath, action)` 包裹调用。

早期实现：

```java
synchronized (UserGroupInformation.class) {
    System.setProperty("java.security.krb5.conf", krb5ConfPath);   // 全局
    UserGroupInformation.loginUserFromKeytab(principal, keytab);   // 全局
    return executeActionInDoAs(UserGroupInformation.getLoginUser(), action);
}
```

功能上能跑（因为整段是串行的，切换是原子的），但**所有 catalog 的元数据访问全部串行**。
catalog 一多，元数据就成瓶颈。

优化思路是加一条无锁快路径。但有个坑：

**实际部署的 `HiveMetaClient` 调的是 4 参数版**，`krb5ConfPath` 来自
`hive.metastore.kerberos.krb5.conf`，**永远非 null**。
所以最初写的 `if (krb5ConfPath == null)` 快路径条件永远进不去 ——
部署后日志里只有 HDFS UGI、没有 HMS UGI，看起来像没生效。

进一步核对发现：FE 启动参数 `-Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf`
和 catalog 里配的 `hive.metastore.kerberos.krb5.conf` **指向同一个文件**（md5 一致），
而且这个文件已经包含全部 realm。**那次 swap 是纯空操作，却付出了全量串行的代价。**

所以条件放宽为 `canSkipKrb5Swap()`：

```java
private static boolean canSkipKrb5Swap(String krb5ConfPath) {
    if (krb5ConfPath == null) return true;
    String current = System.getProperty("java.security.krb5.conf");
    if (current == null) return false;
    if (krb5ConfPath.equals(current)) return true;
    // 路径写法不同但其实是同一文件
    return new File(krb5ConfPath).getCanonicalFile()
            .equals(new File(current).getCanonicalFile());
}
```

满足时走 `getOrCreateKeytabUGI()`（与 BE 侧共用的独立 UGI 缓存），
无全局锁、不改全局 loginUser。不满足时 fall through 到原来的串行路径，正确性不受影响。

**前提**：单个 krb5.conf 必须包含所有 realm + 对应的 `[domain_realm]` host 映射。
这本来也是多集群场景的推荐配置。

## 两条走不通的路

### C++ 层 `setenv("KRB5CCNAME")`

在 `be/src/fs/hdfs/hdfs_fs_cache.cpp` 里给每个 catalog 算 hash，
`setenv` 成不同的 ticket cache 路径。

**无效。** BE 通过 libhdfs 走 JNI，真正建连的是 JVM 里的 Java 代码，
而 Java 的 `System.getenv()` 读的是 **JVM 启动时的环境快照** ——
进程运行期再 `setenv` 对 JVM 完全不可见。

详细证伪过程见 `patches/obsolete/WHY_OBSOLETE.md`。

### BE 启动前 `kinit`

在 `start_be.sh` 里 `kinit -kt /etc/be.keytab ...`，配合
`KRB5CCNAME=FILE:/tmp/krb5cc_be`。

单集群没问题，多 realm 天然不行 —— 一个 ticket cache 只能是一个身份。
这正是问题本身，不是解法。

## krb5 配置的两个必需项

**`[domain_realm]` host 映射。**
Hive 的 SASL 用 hostbased 规范化，`hive/hive-c@EXAMPLE.COM` 会被拆成
`hive@hive-c`（**realm 被丢掉**），再由 `[domain_realm]` 反查 host 属于哪个 realm。
缺少 `hive-c → EXAMPLE.COM` 映射就会回落到 `default_realm`，
跨域请求直接 `error code 7` 或 `No service creds`。

```ini
[domain_realm]
    hive-c  = EXAMPLE.COM
    .hive-c = EXAMPLE.COM
    hacluster = EXAMPLE.COM
    arm-ha  = HIVE_ARM.TEST
```

nameservice 名（`hacluster` / `arm-ha`）也要映射 —— HA 模式下客户端会拿它当 host 用。

**`hadoop.security.auth_to_local` 要含所有 realm 的 RULE。**
否则报 `KerberosName$NoMatchingRule`。配在 BE/FE 的 `core-site.xml` 里。

## 属性前缀

FE 的 `HDFSCloudCredential.toThrift()` 只透传这四类前缀到 BE：

```
dfs.    hadoop.    ipc.    hive.
```

**`hdfs.kerberos.principal` 到不了 BE。** catalog 里必须用 `hadoop.` 前缀：

```sql
"hadoop.security.authentication" = "kerberos",
"hadoop.kerberos.principal"      = "user_c@EXAMPLE.COM",
"hadoop.kerberos.keytab"         = "/opt/starrocks/krb5/user_c.keytab"
```

`getHDFSUGI()` 里 `PRINCIPAL_KEYS` / `KEYTAB_KEYS` 各接受三种写法作为兼容，
但只有 `hadoop.` 开头的能真正传到 BE。

## 怎么确认真的生效了

**看日志。** 每个 catalog 首次访问时各打一条：

```
be.out: [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=user_c@EXAMPLE.COM
be.out: [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=user_arm@HIVE_ARM.TEST
fe.out: [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=user_c@EXAMPLE.COM
fe.out: [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=user_arm@HIVE_ARM.TEST
```

**在没有 ticket cache 的环境下验证。** 这一条最重要：
有 ticket cache 时，即使代码没生效也可能碰巧查通。
删掉所有 `/tmp/krb5cc_*` 和 kinit 守护进程后仍能查，才算数。

完整验证方法见主 README 第 8 节和 `deploy/verify_multi_kerberos.sh`。

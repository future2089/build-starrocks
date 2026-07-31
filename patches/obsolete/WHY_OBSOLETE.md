# 为什么这些补丁被废弃

本目录保存历史尝试，**不参与构建**。`apply_patches.sh` 不会应用其中任何一个。

保留它们的唯一目的：记录已经走过的死胡同，避免后来者重复。

---

## starrocks-be.patch — BE C++ 层 per-catalog Kerberos（已证伪）

**曾经的设想**：在 `be/src/fs/hdfs/hdfs_fs_cache.cpp` 的 `create_hdfs_fs_handle()` 里，
按 catalog 的 keytab/principal 算一个 hash，`setenv("KRB5CCNAME", "/tmp/starrocks_krb5cc_<hash>")`，
让每个 catalog 用独立的 Kerberos ticket cache；同时给 `FSOptions` 加 `catalog_id` 字段，
把它拼进 `HdfsFsCache` 的 cache key。

**三条独立的证伪依据**：

**① `setenv` 对 JVM 不可见。**
BE 通过 libhdfs 调用 JNI，真正建连的是 JVM 内的 Java 代码。而 Java 的 `System.getenv()`
读的是 **JVM 启动时的环境快照**，进程运行期再 `setenv` 不会反映到 JVM 里。
所以这段代码即便执行了，Java 侧的 Kerberos 登录仍然读原来的 `KRB5CCNAME`。

**② `catalog_id` 从来没有被赋值。**
patch 只在 `fs.h` 里加了 `std::string catalog_id;` 字段声明，并在
`HdfsFsCache::get_connection()` 里把它拼进 cache key，
但**没有任何一处代码给它赋值**。它永远是空串，cache key 退化成 `":" + namenode`，
与未打补丁时完全等价。

**③ 线上二进制根本没含它，却已全功能通过。**
现网运行的 `starrocks_be` 是 2026-07-16 编译的，早于本 patch 的源码改动日期（07-17），
从未被编译进去。而 2026-07-31 的验证显示：两个不同 realm 的 Hive 集群
（EXAMPLE.COM / HIVE_ARM.TEST）可以同时查询、跨集群 JOIN，
在系统内**没有任何 ticket cache** 的条件下依然成功。

**真正的解在 Java 层。**
StarRocks 把定制的 `org/apache/hadoop/fs/FileSystem.class` 打进
`starrocks-hadoop-ext.jar`，并放在 BE CLASSPATH **首位**覆盖 Hadoop 原版。
其 `createFileSystem(URI, Configuration)` 里有钩子：

```java
HadoopExt.getInstance().rewriteConfiguration(conf);
UserGroupInformation ugi = HadoopExt.getInstance().getHDFSUGI(conf);
return HadoopExt.getInstance().doAs(ugi, () -> /* 真正创建 FS */);
```

社区版 `getHDFSUGI()` 是空实现返回 `null` → `doAs(null, ...)` 退化为 JVM 全局
`loginUser` → 所有 catalog 共用一个 Kerberos 身份 → 多 realm 互斥。

补上 `getHDFSUGI()` 的实现即可，**完全不需要动 C++**。
详见 `docs/kerberos-isolation.md` 与 `patches/HadoopExt.java`。

**如果将来仍需要 catalog_id：** 唯一有价值的场景是两个集群的 nameservice **同名**
（比如都叫 `nameservice1`），此时 `HdfsFsCache` 会错误复用 FS handle。
当前环境 nameservice 分别是 `hacluster` 和 `arm-ha`，不冲突。
真要做，需要补齐 `catalog_id` 的赋值链路（FE thrift → BE `FSOptions`），
而不是照搬这个 patch。

---

## starrocks-be-per-catalog-kerberos.patch

同一思路的更早版本，问题相同。

## starrocks-fixes.patch

早期混合补丁，其中有效的部分已拆分并合入 `patches/starrocks-fe.patch`。

## modify_hdfs_cache.py / modify_hdfs_provider.py / modify_toThrift.py

早期用 Python 脚本做正则替换源码的做法，脆弱且不可重复。
已被 `git apply` + 标准 `.patch` 文件取代。

# patches/ — 源码补丁

对 StarRocks **3.3.17 (3eac4a9)** 的源码改动。走**全量编译**路径时使用。

> 已经有在跑的集群？不要走这里。用 `../deploy/hotpatch_hadoop_ext.sh`，
> 免重编译，5 分钟内让改动生效。

## 补丁清单

| 文件 | 层 | 作用 | 必需性 |
|---|---|---|---|
| `HadoopExt.java` | FE + BE | **per-catalog 独立 UGI**。BE 侧实现 `getHDFSUGI()`，FE 侧给 `doAsWithSwap()` 加无锁快路径 | **★ 核心，缺它整套方案不成立** |
| `starrocks-fe.patch` → `HiveMetaClient.java` | FE | 读 catalog 的 `hive.metastore.kerberos.*`，用 `doAsWithSwap()` 包裹 HMS RPC | 必需 |
| `starrocks-fe.patch` → `HDFSCloudCredential.java` | FE | 实现 `toThrift()`（透传 `dfs./hadoop./ipc./hive.` 前缀属性到 BE）与 `applyToConfiguration()` | 必需（HDFS HA 透传） |
| `starrocks-fe.patch` → `HDFSCloudConfigurationProvider.java` | FE | 允许用标准 Hadoop key（`hadoop.security.krb5.principal` / `hadoop.security.keytab.file`）通过 FE 侧凭据校验 | 必需 |
| `obsolete/starrocks-be.patch` | BE (C++) | ~~per-catalog KRB5CCNAME~~ | **已废弃**，见 `obsolete/WHY_OBSOLETE.md` |

**没有 BE C++ 补丁。** 早期尝试过在 `hdfs_fs_cache.cpp` 里 `setenv("KRB5CCNAME")`，
已被三条证据证伪（`setenv` 对 JVM 不可见 / `catalog_id` 从未赋值 / 线上二进制未含它却全通）。
真正的解全在 Java 层。

## 一个必须知道的坑

**`HadoopExt.java` 不在 `.patch` 文件里。**

它是整份改动量最大的文件，用 `git apply` 打不进去，必须由 `apply_patches.sh`
额外 `cp` 到**两个位置**：

```
fe/fe-core/src/main/java/com/starrocks/connector/hadoop/HadoopExt.java
    → 编译进 starrocks-fe.jar，FE 用（HMS 认证）

java-extensions/hadoop-ext/src/main/java/com/starrocks/connector/hadoop/HadoopExt.java
    → 编译进 starrocks-hadoop-ext.jar，BE 用（HDFS 认证）
```

两份内容必须**完全一致**。只 `git apply` 不跑脚本，会得到一个能编译、能启动、
单集群也能查，但**多 realm 一定串扰**的版本 —— 而且不报错，只是第二个 catalog
查不出来。

`apply_patches.sh` 末尾会校验两份文件里都有
`getHDFSUGI` / `getOrCreateKeytabUGI` / `loginUserFromKeytabAndReturnUGI`。

## 用法

```bash
cd /data/starrocks-build/starrocks-3.3.17
bash /path/to/patches/apply_patches.sh

# FE
cd fe && mvn package -DskipTests -Dcheckstyle.skip=true

# BE（cc1plus 约 4GB/进程，先加 swap，别开满核）
./build.sh --be -j 2
```

## 版本适配

只有 3.3.x 能干净 apply。3.4+ 上游重构了 `HiveMetaClient`（加了 HMS 连接池）
和 BE 的 `FSOptions`，需要手工 re-base。详细评估见
`../docs/patch_migration_assessment.md`。

`HDFSCloudCredential.toThrift()` 直到 4.0 仍是空实现 —— 说明这个能力缺口
上游至今没补，补丁依然有价值。

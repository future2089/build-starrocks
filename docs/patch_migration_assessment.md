# 补丁迁移成本评估报告

- 基准版本: **StarRocks 3.3.17**（本项目补丁基线）
- 评估日期: 2026-07-30
- 评估方法: 将本项目 5 个补丁锚点文件，逐一对比官方 `branch-3.5` 与 `branch-4.0` 源码结构
- 当前最新版: **v4.0.13**（2026-07-16）；3.5.x 线已发布（3.5.0 ≈ 2026-03）

---

## 一、补丁清单与逐文件结论

本项目补丁共 5 个锚点（FE 3 + BE 2）：

| 文件                              | 在 3.5/4.0 的状态                                                                                                                               | 是否干净 apply        | 迁移成本   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | ------ |
| `HDFSCloudCredential.java` (FE) | **结构完全一致**，`applyToConfiguration`/`toThrift` 仍是空 stub                                                                                       | ✅ 基本可直接 apply     | **低**  |
| `HadoopExt.java` (FE)           | **结构完全一致**，`doAsWithSwap` 上游不存在（纯增量）                                                                                                        | ✅ 可直接 apply       | **低**  |
| `HiveMetaClient.java` (FE)      | **已重构**：新增 HMS 连接池（`clientPool`/`maxPoolSize`/`clientPoolLock`）、`callRPC` 双参→三参委托、`finally` 用 `client.finish()/close()`、构造函数设 `maxPoolSize` | ❌ 无法干净 apply      | **中**  |
| `fs.h` → `FSOptions` (BE)       | **已重构**：新结构体（多构造函数 + `_fs_options` map + `hdfs_properties()`），**无 `catalog_id`**                                                            | ❌ 无法 apply（结构体已变） | **中**  |
| `hdfs_fs_cache.cpp` (BE)        | cache key = `namenode + hdfs_username + cloud_properties`；配置经 `hdfsBuilderConfSetStr` 注入；**无任何 kerberos/keytab/krb5 处理**                    | ❌ 注入点已变           | **中高** |

### 关键事实

1. `HDFSCloudCredential.toThrift(Map)` 在 4.0 **仍是空实现** —— 说明 StarRocks 官方至今仍未原生把 `dfs.*`/`hadoop.*` 透传到 BE。本项目的需求缺口依然存在，补丁仍有价值。
2. BE 侧 HDFS 配置现在改走 `THdfsProperties` / `TCloudConfiguration` → `cloud_properties`，而非我们补丁里用的 `FSOptions.catalog_id`。这是 BE 迁移的主要障碍。
3. **HiveMetaClient 连接池**与 **FSOptions 重构**在 3.5 中**已存在**，即在 3.4 就落地了。

---

## 二、核心结论

> **只有停留在 3.3.x 才能 `git apply` 干净应用。一旦升级到 3.4/3.5/4.0，HiveMetaClient 与 BE 两个锚点都必须手动 re-base，且 3.4/3.5/4.0 三者的成本几乎相同**（重构都已在 3.4 完成）。\*\*

因此版本选择不应以"最小化补丁冲突"为依据，而应基于**功能/LTS/社区支持**等其它因素。

| 升级目标                | 补丁工作量  | 说明                           |
| ------------------- | ------ | ---------------------------- |
| 维持 3.3.x（最新 3.3 补丁） | ~0.5 天 | 补丁近乎原样 apply，重编译+回归验证即可      |
| 3.4.x               | ~3–5 天 | 与 3.5/4.0 同量级（重构已存在）         |
| 3.5.x（推荐中间目标）       | ~3–5 天 | 稳定线；功能较 3.3 有提升，补丁成本与 4.0 相同 |
| 4.0.x（最新）           | ~3–5 天 | 最新特性/最长支持；补丁成本与 3.5 相同       |

---

## 三、各锚点迁移要点（re-base 指引）

### 低成本的 FE 两个文件

- **HDFSCloudCredential.java**：类结构未变，`hadoopConfiguration` 字段、构造函数、`toFileStoreInfo()` 均与补丁基线一致。补丁只是把空的 `applyToConfiguration`/`toThrift` 填上实现，可直接套用。
  - ⚠️ 注意：4.0 的 BE 改从 `THdfsProperties`/`cloud_properties` 读取 HDFS 配置，因此 `toThrift` 里 `dfs.*/hadoop.*` 的转发目标可能需要改写到 `THdfsProperties` 载体，否则 BE 端收不到。
- **HadoopExt.java**：`doAs`/`executeActionInDoAs` 及所有 stub 方法签名未变，且上游没有 `doAsWithSwap`，我们新增的方法是纯增量，无冲突。

### 中成本的 `HiveMetaClient.java`（FE）

- 重构点：连接池生命周期（`getClient`/`finish`/`close`）、`callRPC` 委托结构、构造函数。
- re-base 做法：保留"新增 `krbPrincipal`/`krbKeytab` 字段 + 构造器 + 在 `callRPC` 的 `method.invoke` 外包 `doAsWithSwap`"的核心思路，但**手动**把这段代码对齐到新的 `callRPC`（三参重载 + `finally` 池化语义），注意不要破坏 `client.finish()/close()` 逻辑。
- 风险：3.5/4.0 的 `createHiveMetaClient` 额外设置了 `HIVE_METASTORE_CONNECTION_POOL_SIZE`，且 `properties.forEach(conf::set)` 已把 catalog 属性（含 kerberos principal/keytab）透传进 `HiveConf` —— 可利用这点简化 principal/keytab 读取。

### 中高成本的 BE 两个文件

- `FSOptions` 已重构为携带 `TCloudConfiguration`/`THdfsProperties`/`_fs_options` 的结构体，**没有 `catalog_id`**。per-catalog 的 keytab/principal/KRB5CCNAME 注入点需改到新载体（通过 `THdfsProperties` 或 `_fs_options` map 携带，并在 `hdfs_fs_cache.cpp` 的 `create_hdfs_fs_handle` 里应用）。
- `hdfs_fs_cache.cpp` 的 cache key 现在是 `namenode + hdfs_username + cloud_properties`，需把 kerberos 身份也并入 key，避免不同 catalog 的 ticket 串用；并在 `create_hdfs_fs_handle` 中用 `hdfsBuilderConfSetStr` 注入 krb5/keytab 相关配置、设置 `KRB5CCNAME`。

---

## 四、阻塞点 / 风险

1. **BE kerberos 身份（keytab/principal/KRB5CCNAME）在官方代码中完全不存在** → 必须整段 re-port，无现成钩子可复用。
2. **`HDFSCloudCredential.toThrift` 在 4.0 仍为空** → 官方仍未原生支持 `dfs.*` 透传；我们的特性仍必要，但 BE 消费端已换载体，需两端对齐。
3. **HiveMetaClient 连接池生命周期** → re-base 时若 `doAsWithSwap` 包裹位置不当，可能破坏连接回收或引发 UGI 线程安全问题（我们补丁本身用了 `synchronized(UserGroupInformation.class)`，需保留）。
4. **验证环境依赖重** → 任何 re-base 都必须在"双 Kerberos HMS + HDFS HA"多集群环境回归（见 README 验证章节），搭建成本高。

---

## 五、建议与后续动作

1. **版本决策**：若目标是"在新版 StarRocks 上保留该特性"，直接选 **3.5.x 或 4.0.x**（成本相同），不要为省补丁而卡在 3.3.x。
2. **补丁维护方式**：把补丁作为受控 fork diff 维护，迁移时用 `git apply --3way` + 手工解决冲突；为新版本打补丁后跑集成回归。
3. **评估官方是否已原生支持**：4.x 的 `THdfsProperties` 已能携带 HDFS 属性，建议先确认官方是否已在 4.x 支持 per-catalog HDFS HA（HA nameservice 配置），若已支持可砍掉 `HDFSCloudCredential` 转发部分，只保留 kerberos 身份隔离这部分。
4. **BE 优先级**：BE 的 `hdfs_fs_cache.cpp` re-port 工作量最大且验证最重，建议作为迁移的第一块啃下。


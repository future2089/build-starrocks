# ARM64 StarRocks 3.3.17 编译结果

编译日期: 2026-07-22
目标机器: 192.168.0.181 (鲲鹏 920 ARM64, openEuler 24.03, 250GB RAM, 64 核)

## 构建产出

| 文件 | 大小 | 说明 |
|------|------|------|
| `starrocks_be` | **271MB** (Release, stripped) | BE 二进制，ARM aarch64，远程机器 |
| `starrocks-fe.jar` | ~24MB | FE JAR，带 Kerberos 补丁 |
| `starrocks-hadoop-ext.jar` | ~79KB | Hadoop 扩展 JAR，带 `doAsWithSwap` |

> BE 二进制保留在远程: `192.168.0.181:/data/starrocks-src/output/be/lib/starrocks_be`
>
> 构建产物（jar 文件）体积较大，仅保留在远程编译环境，不纳入 Git 仓库。

## 编译耗时

| 阶段 | 耗时 | 状态 |
|------|------|------|
| 源码下载 (GitHub tarball, 213MB) | ~35 分钟 | ✅ |
| BE 编译 (64 核并行) | ~35 分钟 | ✅ |
| FE 编译 | ~10 分钟 | ✅ |
| **总计** | **~80 分钟** | ✅ |

## 应用的补丁

### FE 修改汇总

| 文件 | 修改内容 | 用途 |
|------|----------|------|
| `HDFSCloudCredential.java` | toThrift() 转发 Kerberos 配置到 BE | per-catalog 认证传递 |
| `HadoopExt.java` | doAsWithSwap() per-catalog UGI 切换 + per-catalog krb5.conf 动态替换 | 隔离不同域/KDC 的 Kerberos 上下文 |
| `HiveMetaClient.java` | `createHiveMetaClient()` 中登录 principal 优先读 `hive.metastore.client.kerberos.principal`，未设置时回退到 `hive.metastore.kerberos.principal` | 修复 client principal 与服务 principal 混用导致的 keytab 登录失败 |

### BE 修改
- `be/src/fs/fs.h` — FSOptions 增加 `std::string catalog_id`
- `be/src/fs/hdfs/hdfs_fs_cache.cpp` — per-catalog Kerberos keytab/principal 注入，独立 KRB5CCNAME

### build.sh 修改
- 跳过 `.debuginfo` 独立文件生成，仅执行 `strip --strip-debug`（Release 编译，不输出多余文件）

## 远程编译环境

- 编译镜像: `starrocks/dev-env-centos7:3.3.17` (arm64)
- 容器名: `sr-arm-build`
- 源码目录: `/Bigdata1/starrocks-src/`（容器内: `/data/starrocks-src/`）
- 编译脚本: `/Bigdata1/build-starrocks/build_arm.sh`（本地）→ 需 scp 到远程执行
- 补丁目录: `/Bigdata1/build-starrocks/patches/`

## 部署环境 (sr-deploy)

| 组件 | 位置 | 说明 |
|------|------|------|
| sr-deploy 容器 | `192.168.0.211` | StarRocks FE + BE + Broker + Director |
| FE 安装路径 | `/opt/starrocks/fe/` | 绑挂 `/data/starrocks-build/starrocks-3.3.17/output/fe/` |
| FE Java 参数 | `-Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf` | 全局 Kerberos 配置（含 SR.TEST + ARM.SR.TEST 双域） |
| ARM 集群 KDC | `192.168.0.181:88` | `ARM.SR.TEST` 域，鲲鹏 920 节点原生 KDC |
| ARM HDFS | `192.168.0.181:8020` | Hadoop 3.3.6（HDP 管理），NN + DN |
| ARM HMS | `192.168.0.181:9083` | Apache Hive 3.1.3，MySQL 元数据库，**无 Kerberos** |
| hadoop-arm 容器 | 192.168.0.181 内 | 额外 HMS + Derby 数据库（已失活） |

### 已验证能力
- ✅ Per-catalog `hive.metastore.kerberos.krb5.conf` — FE 动态切换 krb5 配置，连接 ARM.SR.TEST 域 KDC
- ✅ Per-catalog UGI 隔离 — `HadoopExt.doAsWithSwap()` 登录独立 principal 并切换 KRB5CCNAME
- ✅ FE Kerberos SASL 握手 — `starrocks/arm-query@ARM.SR.TEST` 登录 + 获取 `hive/arm-hive@ARM.SR.TEST` 服务票据，GSS 上下文建立成功
- ✅ 跨域 krb5.conf — `[domain_realm]` 映射 `arm-hive`、`192.168.0.181` 到 `ARM.SR.TEST`

### 遗留问题
- ⚠️ ARM HMS（PID 860699）未启用 Kerberos（`hive.metastore.sasl.enabled` 未设置），FE 尝试 SASL 连接时 HMS 无对应处理，导致 `Kerberos login failed: Unable to instantiate HiveMetaStoreClient`
- ⚠️ 修复方向：HMS 侧启用 SASL + 配置 `hive.metastore.kerberos.principal` 和 keytab，或 catalog 侧关闭 SASL 使用 SIMPLE 协议

## 编译方式

```bash
# 指定 Release 模式构建 BE（不生成 debuginfo）
BUILD_TYPE=Release ./build.sh --be -j 64

# 构建 FE（跳过 checkstyle 和测试）
mvn package -Dcheckstyle.skip=true -DskipTests
```

## 验证结果

- ✅ BE 二进制: `ELF 64-bit LSB executable, ARM aarch64`，Release stripped，271MB
- ✅ `starrocks-fe.jar`: 包含 `com.starrocks.connector.hive.HiveMetaClient`（带 Kerberos 补丁）
- ✅ `starrocks-hadoop-ext.jar`: 包含 `com.starrocks.connector.hadoop.HadoopExt`（带 `doAsWithSwap` 补丁）
- ✅ `Version.java` 已生成（版本信息正确注入）
- ✅ HadoopExt.java checkstyle: 0 violations

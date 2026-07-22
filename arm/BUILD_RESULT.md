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

### BE 修改
- `be/src/fs/fs.h` — FSOptions 增加 `std::string catalog_id`
- `be/src/fs/hdfs/hdfs_fs_cache.cpp` — per-catalog Kerberos keytab/principal 注入，独立 KRB5CCNAME

### FE 修改
- `HDFSCloudCredential.java` — toThrift() 转发 Kerberos 配置到 BE
- `HadoopExt.java` — doAsWithSwap() per-catalog UGI 切换，修复 12 个 checkstyle 违规
- `HiveMetaClient.java` — RecyclableClient 创建在 doAsWithSwap action 内

### build.sh 修改
- 跳过 `.debuginfo` 独立文件生成，仅执行 `strip --strip-debug`（Release 编译，不输出多余文件）

## 远程编译环境

- 编译镜像: `starrocks/dev-env-centos7:3.3.17` (arm64)
- 容器名: `sr-arm-build`
- 源码目录: `/Bigdata1/starrocks-src/`（容器内: `/data/starrocks-src/`）
- 编译脚本: `/Bigdata1/build-starrocks/build_arm.sh`（本地）→ 需 scp 到远程执行
- 补丁目录: `/Bigdata1/build-starrocks/patches/`

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

# ARM64 StarRocks 3.3.17 编译结果

编译日期: 2026-07-21
目标机器: 192.168.0.181 (鲲鹏 920 ARM64, openEuler 24.03, 250GB RAM, 64 核)

## 构建产出

| 文件 | 大小 | 架构 | 说明 |
|------|------|------|------|
| [starrocks_be](output/starrocks_be) | 1.5GB | ARM aarch64 | BE 二进制（远程机器） |
| [starrocks-fe.jar](starrocks-fe.jar) | 24MB | 跨平台 | FE JAR |
| [starrocks-hadoop-ext.jar](starrocks-hadoop-ext.jar) | 79KB | 跨平台 | Hadoop 扩展 JAR |

**BE 二进制（1.5GB）保留在远程:** `192.168.0.181:/Bigdata1/build-starrocks/output/starrocks_be`

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
- `HadoopExt.java` — doAsWithSwap() per-catalog UGI 切换
- `HiveMetaClient.java` — RecyclableClient 创建在 doAsWithSwap action 内

## 远程编译环境

- 编译镜像: `starrocks/dev-env-centos7:3.3.17` (arm64)
- 容器名: `sr-arm-build`
- 源码目录: `/Bigdata1/starrocks-src/`
- 编译脚本: `/Bigdata1/build-starrocks/build_arm.sh`
- 补丁目录: `/Bigdata1/build-starrocks/patches/`

## 验证结果

- ✅ BE 二进制: `ELF 64-bit LSB executable, ARM aarch64`
- ✅ `starrocks-fe.jar`: 包含 `com.starrocks.connector.hive.HiveMetaClient`（带 Kerberos 补丁）
- ✅ `starrocks-hadoop-ext.jar`: 包含 `com.starrocks.connector.hadoop.HadoopExt`（带 `doAsWithSwap` 补丁）
- ✅ `Version.java` 已生成（版本信息正确注入）

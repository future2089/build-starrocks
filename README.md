# Build StarRocks — 多 Hive Catalog 连接不同安全 HA HDFS 集群

## 概述

本项目对 StarRocks 3.3.17 进行源码修改和编译，实现以下能力：

1. **HDFS HA 配置透传** — 将 Catalog 级别的 `hdfs-site.xml`/`core-site.xml`（HA nameservice 配置）从 FE 传递到 BE
2. **Per-catalog Kerberos 隔离** — 不同的 Hive Catalog 使用不同的 Kerberos principal/keytab 连接 Hive Metastore 和 HDFS
3. **多 Hive Catalog 连接** — 单个 StarRocks 集群同时连接多个不同的安全 Hive 集群

## 环境

| 组件 | 版本 | 备注 |
|---|---|---|
| StarRocks | 3.3.17 (3eac4a9) | 源码编译，BE + FE |
| Hadoop | 3.3.6 | 宿主机已有，单节点非 HA 非 Kerberos |
| Hive | 3.1.3 | 宿主机已有 |
| MySQL | 8.0.31 | 宿主机 Hive Metastore 后端 |
| KDC | krb5-server | Docker 容器 (openeuler/openeuler:24.03) |
| 宿主机 | openEuler 24.03 LTS SP2 | 32 CPU, 30GB RAM, 192.168.0.211 |

### Docker 容器

| 名称 | 镜像 | 作用 |
|---|---|---|
| sr-3.3-build | starrocks/dev-env-ubuntu:3.3-latest | StarRocks 编译环境 |
| sr-deploy | starrocks/dev-env-ubuntu:3.3-latest | 部署 StarRocks FE + BE |
| kdc | openeuler/openeuler:24.03 | Kerberos KDC |
| cluster_a | starrocks/dev-env-ubuntu:3.3-latest | Hive 集群 A（Kerberos，port 9084） |
| cluster_b | starrocks/dev-env-ubuntu:3.3-latest | Hive 集群 B（Kerberos，port 9085） |

## 源码修改

### 1. HDFSCloudCredential.java

**文件:** `fe/fe-core/src/main/java/com/starrocks/credential/hdfs/HDFSCloudCredential.java`

**修改内容:**
- 添加 `Map<String, String> hadoopConfiguration` 字段（已存在于构造函数中）
- **TODO:** 实现 `applyToConfiguration()` — 将 `hadoopConfiguration` 注入 Hadoop Configuration
- **TODO:** 实现 `toThrift()` — 将 HA + Kerberos 配置序列化到 BE

当前状态：构造器已存储 `hadoopConfiguration`，但两个方法尚未实现（空方法体）。

### 2. HadoopExt.java

**文件:**
- `fe/fe-core/src/main/java/com/starrocks/connector/hadoop/HadoopExt.java`
- `java-extensions/hadoop-ext/src/main/java/com/starrocks/connector/hadoop/HadoopExt.java`

两个版本内容相同。

**修改内容 — 新增 `doAsWithSwap()` 方法:**

```java
public <R, E extends Exception> R doAsWithSwap(String krbPrincipal, String krbKeytab,
                                                  GenericExceptionAction<R, E> action) throws E {
    if (krbPrincipal == null || krbKeytab == null) {
        return action.run();
    }
    synchronized (UserGroupInformation.class) {
        try {
            UserGroupInformation.loginUserFromKeytab(krbPrincipal, krbKeytab);
            UserGroupInformation ugi = UserGroupInformation.getLoginUser();
            return executeActionInDoAs(ugi, action);
        } catch (IOException e) {
            throw new RuntimeException("Kerberos login failed for " + krbPrincipal, e);
        }
    }
}
```

**注意:** `loginUserFromKeytab()` 在 Hadoop 中需要 `hadoop.security.authentication=kerberos` 配置才能生效，否则直接返回当前 OS 用户。

### 3. HiveMetaClient.java

**文件:** `fe/fe-core/src/main/java/com/starrocks/connector/hive/HiveMetaClient.java`

**修改内容:**
- 添加 `krbPrincipal` 和 `krbKeytab` 字段
- 新增带 Kerberos 参数的构造器
- `createHiveMetaClient()` 从 properties 读取 `hive.metastore.kerberos.principal` 和 `hive.metastore.kerberos.keytab`
- `callRPC()` 方法中用 `doAsWithSwap()` 包装 Hive Metastore RPC 调用

## 编译

### BE 编译

```bash
./build.sh --be --clean   # 首次清理编译
./build.sh --be -j 2      # 2 核并行（32核机器但每 cc1plus 进程~4GB）
```

**注意:** 30GB 内存 + 多核编译时，cc1plus 每个进程占用 ~4GB，容易 OOM。需要添加 swap：
```bash
dd if=/dev/zero of=/data/swapfile bs=1M count=16384
chmod 600 /data/swapfile
mkswap /data/swapfile
swapon /data/swapfile
```

### FE 编译

```bash
mvn package -Dcheckstyle.skip=true  # 跳过 checkstyle（ANTLR 解析问题）
```

## 测试环境搭建

### 1. KDC 部署

```bash
docker run -d --name kdc --network host \
  -v /data/starrocks-deploy:/data/starrocks-deploy \
  openeuler/openeuler:24.03 sleep infinity
```

配置 KDC 数据库、创建 principals 和 keytabs（详情见 `scripts/setup_kdc.py`）。

Keytabs 包含：
- `hive/localhost@SR.TEST` — Hive Metastore server principal（两个 cluster 共用）
- `hive/cluster_a@SR.TEST` — Cluster A 专用 principal
- `hive/cluster_b@SR.TEST` — Cluster B 专用 principal

**注意:** KVNO 同步问题 — 每次 `ktadd` 会递增 KVNO，需使用 `-norandkey` 标志。

### 2. Hive 集群部署

每个集群使用 dev-env-ubuntu 容器，挂载宿主机 Hadoop/Hive 二进制：

```bash
docker run -d --name cluster_a --network host \
  -v /data/bigdata/hadoop-3.3.6:/usr/local/hadoop:ro \
  -v /data/bigdata/apache-hive-3.1.3-bin:/usr/local/hive:ro \
  -v /data/starrocks-deploy/cluster_a:/data/deploy \
  starrocks/dev-env-ubuntu:3.3-latest sleep infinity
```

关键配置差异：

| 项目 | cluster_a | cluster_b |
|---|---|---|
| Hive 数据库 | `hive_a` | `hive_b` |
| HMS 端口 | `9084` | `9085` |
| 仓库目录 | `/user/hive_a/warehouse` | `/user/hive_b/warehouse` |
| Nameservice | `nameservice_a` | `nameservice_b` |
| Kerberos 主体 | `hive/localhost@SR.TEST` | `hive/localhost@SR.TEST` |

### 3. 已知问题与解决方案

#### Q: `Kerberos principal should have 3 parts: root`

**原因:** Hadoop 的 `UserGroupInformation.loginUserFromKeytab()` 在 `hadoop.security.authentication` 未设置为 `kerberos` 时直接返回当前 OS 用户，不执行 Kerberos 登录。

**解决方案:** 在 `core-site.xml` 中设置：
```xml
<property>
    <name>hadoop.security.authentication</name>
    <value>kerberos</value>
</property>
<property>
    <name>ipc.client.fallback-to-simple-auth-allowed</name>
    <value>true</value>
</property>
```

同时需要在 JVM 启动参数中指定 krb5.conf 和 JAAS 配置：
```
-Djava.security.krb5.conf=/path/to/krb5.conf
-Djava.security.auth.login.config=/path/to/jaas.conf
```

#### Q: `NoSuchMethodError: HadoopExt.doAsWithSwap`

**原因:** `starrocks-hadoop-ext.jar` 和 `starrocks-fe.jar` 都包含 `HadoopExt.class`，JVM 加载了旧版本的 `starrocks-hadoop-ext.jar`。

**解决方案:** 从 `starrocks-fe.jar` 提取更新后的 `HadoopExt.class` 和 `GenericExceptionAction.class` 覆盖到 `starrocks-hadoop-ext.jar`。

## 验证

### 基本多 Catalog 查询

```sql
CREATE EXTERNAL CATALOG hive_a PROPERTIES (
    "type"="hive",
    "hive.metastore.uris"="thrift://192.168.0.211:9084"
);

CREATE EXTERNAL CATALOG hive_b PROPERTIES (
    "type"="hive",
    "hive.metastore.uris"="thrift://192.168.0.211:9085"
);

SELECT * FROM hive_a.test_db.users;      -- 1 Alice 30 / 2 Bob 25
SELECT * FROM hive_b.test_db.products;   -- 101 Widget 9.99 / 102 Gadget 19.99
```

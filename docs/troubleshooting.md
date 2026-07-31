# 排障速查

按**症状**查。每条给根因和处置。

## 认证类

### `KrbApErrException: Fail to create credential. (63) - No service creds`

出现在 BE（HDFS 访问）或 FE（HMS 访问）。三种可能，按可能性排序：

**① per-catalog UGI 没生效（最常见）**

判断：查询是否呈现"**完美对称性**" —— 系统默认 ticket cache 里是谁，
哪个 catalog 就通，另一个必挂。是的话就是这个。

```bash
klist                      # 看当前默认 ccache 是谁
grep "per-catalog" be.out  # 应该每个 catalog 各一条
grep "per-catalog" fe.out
```

没有日志说明 `getHDFSUGI` 没被调到，检查：
- jar 是否真的打上了？`javap -p -c -cp <jar> com.starrocks.connector.hadoop.HadoopExt | grep loginUserFromKeytabAndReturnUGI`
- **FE 和 BE 两份 jar 都打了吗**？两个位置不同的文件，很容易只打一个
- 打完重启了吗？

**② catalog 属性用错了前缀**

`hdfs.kerberos.principal` 传不到 BE。FE 的 `toThrift()` 只透传
`dfs.` / `hadoop.` / `ipc.` / `hive.` 四类前缀。改用 `hadoop.kerberos.principal`。

**③ krb5.conf 缺 `[domain_realm]` 映射**

Hive SASL 把 `hive/hive-c@EXAMPLE.COM` 规范化成 `hive@hive-c`（丢 realm），
靠 `[domain_realm]` 反查 host 的 realm。缺映射会回落到 `default_realm`，跨域失败。

要映射的不只是主机名，**HA nameservice 名也要**：

```ini
[domain_realm]
    hive-c    = EXAMPLE.COM
    .hive-c   = EXAMPLE.COM
    hacluster = EXAMPLE.COM
    arm-ha    = HIVE_ARM.TEST
```

验证 KDC 侧是否正常：`kvno nn/hive-c@EXAMPLE.COM` —— 能拿到 kvno 说明 KDC 没问题，
问题在客户端配置。

### `KerberosName$NoMatchingRule: No rules applied to xxx@REALM`

`core-site.xml` 的 `hadoop.security.auth_to_local` 没覆盖这个 realm。
多集群时**每个 realm 都要有 RULE**。改 BE/FE 的 `core-site.xml` 后重启。

### `Kerberos principal should have 3 parts: root`

`hadoop.security.authentication` 没设成 `kerberos`。
Hadoop 的 `loginUserFromKeytab()` 在非安全模式下会直接返回当前 OS 用户，不做登录。

代码里 `ensureKerberosEnabled()` 会兜底处理，但配置该配还是要配。

### `SIMPLE authentication is not enabled. Available:[TOKEN, KERBEROS]`

NameNode 开了 Kerberos，客户端没带凭据。检查 catalog 的
`hadoop.security.authentication` / `hadoop.kerberos.principal` / `hadoop.kerberos.keytab`
三件套是否齐全，以及 **keytab 文件在 BE 进程里可读**（权限 644，路径存在）。

### FE 日志只有 HDFS UGI、没有 HMS UGI

`doAsWithSwap` 的快路径没进去。

实际部署的 `HiveMetaClient` 是 4 参数版，`krb5ConfPath` 来自
`hive.metastore.kerberos.krb5.conf`，永远非 null。
确认 `HadoopExt` 里是 `canSkipKrb5Swap()` 而不是 `krb5ConfPath == null`。

```bash
javap -p -c -cp "starrocks-fe.jar:/opt/starrocks/fe/lib/*" \
  com.starrocks.connector.hive.HiveMetaClient | grep -A1 doAsWithSwap
```

## 部署类

### 只更新了一个 jar

**FE 和 BE 各有一份独立的 `starrocks-hadoop-ext.jar`**：

```
/opt/starrocks/fe/lib/starrocks-hadoop-ext.jar
/opt/starrocks/be/lib/jni-packages/starrocks-hadoop-ext.jar
```

两个不同文件，都在各自 CLASSPATH 首位。只打一个的表现是"一半生效"
（比如 HDFS 隔离好了但 HMS 还串行）。`deploy/hotpatch_hadoop_ext.sh` 默认两个都打。

### `start_be.sh` / `start_fe.sh` 拒绝启动

`sr` 容器 PID 1 不 reap 子进程，旧进程变 `<defunct>` 僵尸，残留的
`be.pid` / `fe.pid` 让启动脚本认为服务还在跑。

```bash
kill <pid>; sleep 3
rm -f /opt/starrocks/be/bin/be.pid
nohup /opt/starrocks/be/bin/start_be.sh --daemon </dev/null >/dev/null 2>&1 & disown
```

用 `deploy/restart_be.sh` / `restart_fe.sh`，已经处理了这些。

### ssh 执行 `pkill -f starrocks_be` 后连接直接断（exit 255）

`-f` 匹配完整命令行，`docker exec ... starrocks_be` 自身也匹配上了，
把 exec 一起杀掉。**用精确 pid kill**，不要用 `pkill -f`。

### 远程命令看似执行了但没有输出

`ssh "docker exec ... 'cmd'"` 多层引号嵌套会吞输出。

固定做法：本地写脚本 → `scp` 到宿主机 → `docker cp` 进容器 → `docker exec bash 脚本`。

另外 `docker exec -i` 不加载登录 profile，脚本里要显式 `export JAVA_HOME` 和 `PATH`。

### 查询结果没变化 / 改了配置不生效

StarRocks 会缓存外表元数据。要真正打到 HMS/HDFS 必须：

```sql
REFRESH EXTERNAL TABLE <catalog>.<db>.<table>;
```

排查日志时也要注意这点 —— 不 REFRESH 就查，日志里什么都不会新增。

## 日志判读

### 分不清报错是新增的还是历史遗留

fe.out / be.out 动辄几万行，旧 jar 时期的报错会一直躺在里面。

**打标记法**：

```bash
MARK="=== PROBE $(date +%s) ==="
echo "$MARK" >> fe.out
mysql -e "REFRESH EXTERNAL TABLE hive_catalog.default.test_tbl; SELECT ..."
sed -n "/$MARK/,\$p" fe.out | grep -i "error\|exception"
```

只看标记之后的内容。零匹配才说明真的没问题。

### 想确认并发是否真的不串行了

压测的同时抓线程栈，直接看有没有线程卡在 UGI 全局锁上：

```bash
jstack <fe_pid> > /tmp/st.txt
grep -c "waiting to lock.*UserGroupInformation" /tmp/st.txt   # 应为 0
grep -c "java.lang.Thread.State: BLOCKED" /tmp/st.txt         # 应为 0
```

## HDFS / Hive 环境类

### `Could not obtain block: ... No live nodes contain current block`

DataNode 用 `localhost` 注册成了 `127.0.0.1:9866`，BE 容器里访问不到。
在 `hdfs-site.xml` 设 `dfs.datanode.hostname=<实际IP>` 后重启 DN。

### DataNode 起不来，日志报 block pool ID 不匹配

NameNode 被 reformat 过而 DN 没同步。
确认 DN 上没有真实数据后清空 `dfs.datanode.data.dir` 重启即可。

**先确认没数据再动。**

### `hive` CLI 卡住不返回

大概率 NameNode 挂了 —— CLI 会卡在创建 HDFS scratchdir。

不要靠 CLI 判断 HMS 死活，改看 `hive.log` 的审计日志，或直接查 MySQL 元数据库。

### `count(*)` 返回 0 但表里明明有数据

Hive 默认读 metastore 的统计信息，stats 过期了。

```sql
set hive.compute.query.using.stats=false;
-- 或
ANALYZE TABLE <t> COMPUTE STATISTICS;
```

## 编译类

### BE 编译 OOM

`cc1plus` 每进程约 4GB。32 核机器也不要开满：

```bash
./build.sh --be -j 2
```

内存不够先加 swap：

```bash
dd if=/dev/zero of=/data/swapfile bs=1M count=16384
chmod 600 /data/swapfile && mkswap /data/swapfile && swapon /data/swapfile
```

### `git apply` 打 patch 冲突

只有 3.3.x 能干净 apply。3.4+ 上游重构了 `HiveMetaClient`（加了 HMS 连接池）
和 BE 的 `FSOptions`。见 `patch_migration_assessment.md`。

### 编译通过、启动正常、但多 realm 还是串扰

`HadoopExt.java` **不在 `.patch` 文件里**，`git apply` 打不进去。
必须跑 `patches/apply_patches.sh`，它会额外 `cp` 到两个源码位置。

只 apply patch 得到的版本能编译、能启动、单集群能查，但多 realm 一定失败 —— 且不报错。

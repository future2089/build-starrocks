# deploy/ — 运行期脚本

对**已经在跑**的 StarRocks 集群做热部署、重启和验证。不涉及源码编译。

源码改动在 `../patches/`。两者的分工：

| | patches/ | deploy/ |
|---|---|---|
| 场景 | 从源码构建新版本 | 已有集群，想让改动立刻生效 |
| 手段 | `git apply` + `mvn` / `build.sh` | `javac` + `jar uf` 写回已部署的 jar |
| 耗时 | FE 十几分钟，BE 数小时 | 约 5 分钟 |
| 产物 | 新的 `output/{fe,be}` | 原地更新 jar，自动备份 |

热部署只能改 **Java 类**。BE 的 C++ 二进制改不了 —— 好在本方案不需要动 C++。

## 脚本

### `hotpatch_hadoop_ext.sh`

把 `patches/HadoopExt.java` 编译后写回已部署的 `starrocks-hadoop-ext.jar`。

**FE 和 BE 各有一份独立的 jar，位置不同，必须都打**：

```
FE: /opt/starrocks/fe/lib/starrocks-hadoop-ext.jar             ← CLASSPATH 首位
BE: /opt/starrocks/be/lib/jni-packages/starrocks-hadoop-ext.jar
```

两者都排在各自 CLASSPATH 最前，会覆盖 `starrocks-fe.jar` 里的同名类。
**曾经只更新 BE 那份**，结果 HDFS 隔离生效了、HMS 侧却还在串行 —— 排查了很久。

```bash
bash hotpatch_hadoop_ext.sh              # 默认两个都打
bash hotpatch_hadoop_ext.sh <jar路径>     # 只打指定的
```

自动备份为 `.orig`（首次）和 `.bak_<时间戳>`（每次）。
回滚：`cp <jar>.orig <jar>` 后重启。

编译 classpath 按 jar 路径自动选：FE 用 `/opt/starrocks/fe/lib/*`，
BE 用 `/opt/starrocks/be/lib/hadoop/common/*`。

打完会校验 `loginUserFromKeytabAndReturnUGI` 和 `getOrCreateKeytabUGI` 是否都在。

### `restart_fe.sh` / `restart_be.sh`

标准重启流程。不要直接用 `stop_fe.sh` / `stop_be.sh`。

`sr` 容器的 PID 1 不 reap 子进程，旧进程会变成 `<defunct>` 僵尸，
而残留的 `fe.pid` / `be.pid` 会让 `start_*.sh` 直接拒绝启动。
脚本做的事：精确 pid kill → 等进程消失 → `rm -f *.pid` →
`nohup ... </dev/null & disown` → 轮询直到可用。

`restart_fe.sh` 还会校验 `SHOW FRONTENDS` 的 `Role=LEADER`。

> **不要用 `pkill -f starrocks_be`。** 模式串会匹配到
> `docker exec ... starrocks_be` 命令行自身，把 exec 一起杀掉，
> ssh 直接以 255 退出，什么输出都拿不到。

### `verify_multi_kerberos.sh`

端到端验证。检查项：

1. 系统内**不存在**任何 ticket cache（`/tmp/krb5cc_*`、`/opt/starrocks/krb5/cc_*`）
2. BE Alive
3. `SHOW CATALOGS` 列出全部 catalog
4. 两个 catalog 分别出数
5. 跨集群 JOIN
6. `be.out` / `fe.out` 里每个 catalog 各有一条 per-catalog UGI 日志

第 1 条是关键。有 ticket cache 时即使代码没生效也可能"碰巧"查通，
必须在没有任何 cache 的裸环境下验证，才能证明走的确实是 per-catalog keytab。

### `multi_kerberos_catalogs.sql`

已验证的 catalog 定义模板，含两个不同 realm 的集群。
配置规范（`hadoop.` 前缀、`domain_realm`、`auth_to_local`）见文件内注释和主 README 第 7 节。

## 典型流程

```bash
# 1. 上传源码和脚本到容器
scp patches/HadoopExt.java deploy/*.sh root@192.168.0.211:/tmp/
ssh root@192.168.0.211 'docker exec sr mkdir -p /tmp/hp && \
  for f in HadoopExt.java hotpatch_hadoop_ext.sh restart_fe.sh restart_be.sh; do \
    docker cp /tmp/$f sr:/tmp/hp/; done'

# 2. 热部署 FE + BE 两个 jar
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/hotpatch_hadoop_ext.sh'

# 3. 重启
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/restart_fe.sh'
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/restart_be.sh'

# 4. 验证
ssh root@192.168.0.211 'docker exec sr bash /tmp/hp/verify_multi_kerberos.sh'
```

## 远程执行注意

复杂命令**不要**直接嵌在 `ssh "docker exec ... '...'"` 里。多层引号嵌套会吞掉输出，
表现为命令看似执行了但什么都没返回。

可靠做法固定为：本地写脚本 → `scp` 到宿主机 → `docker cp` 进容器 → `docker exec bash 脚本`。

另外，非交互的 `docker exec -i` 不加载登录 profile，脚本里要显式设置：

```bash
export JAVA_HOME=/usr/lib/jvm/java-11
export PATH=$JAVA_HOME/bin:$PATH
```

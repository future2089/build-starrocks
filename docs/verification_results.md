# 验证结果

最后更新：2026-07-31

## 环境

| | 集群 A | 集群 B |
|---|---|---|
| Catalog | `hive_hivec` | `hive_catalog` |
| 位置 | 192.168.0.211 容器 `hive_c` | 192.168.0.181 容器 `hive_arm`（ARM64） |
| Realm | `EXAMPLE.COM` | `HIVE_ARM.TEST` |
| 客户端身份 | `user_c@EXAMPLE.COM` | `user_arm@HIVE_ARM.TEST` |
| HMS | `:9083` SASL | `:9086` SASL |
| HDFS | HA，nameservice `hacluster` | `arm-ha` |
| KDC | 独立，`:88` | 独立，`:8888` |

两个 realm **无跨域信任**，KDC 完全独立。

## 结论

单个 StarRocks 集群同时访问两个不同 realm 的安全 Hive 集群，
功能与并发均已打通。在**系统内不存在任何 Kerberos ticket cache、
也没有任何 kinit 续期守护进程**的条件下验证通过。

## 三层验证

排障时踩过的坑：有 ticket cache 时，即使代码没生效也可能"碰巧"查通。
所以验证必须分三层，只有第三层通过才算数。

### 第 1 层：有默认 ccache 时能查

基础功能。**不足以证明隔离生效** —— 可能只是碰巧命中了全局身份。

### 第 2 层：对称性实验

把 `/tmp/krb5cc_0` 换成另一个身份，观察哪个 catalog 通。

| `/tmp/krb5cc_0` 里的身份 | `hive_hivec` | `hive_catalog` |
|---|---|---|
| `user_arm@HIVE_ARM.TEST` | `No service creds` | 出数 |
| `user_c@EXAMPLE.COM` | 出数 | `No service creds` |

这个**完美对称**的结果坐实了根因：BE 完全忽略 per-catalog 凭据，只认全局 ccache。
修复后再做这个实验，两个 catalog 应该都不受 ccache 内容影响。

### 第 3 层：无 ccache 裸环境（决定性）

```bash
pkill -f renew.sh                       # 杀掉所有 kinit 续期守护
rm -f /tmp/krb5cc_* /opt/starrocks/krb5/cc_*
klist                                   # 应输出 No credentials cache found
# 重启 FE + BE
```

在这个状态下全部查询仍然成功 —— 证明走的确实是 per-catalog keytab 独立登录。

## 功能验证（第 3 层条件下）

| 项目 | 结果 |
|---|---|
| `klist` | `No credentials cache found` ✓ |
| `/tmp/krb5cc_*` | 不存在 ✓ |
| `/opt/starrocks/krb5/` | 只剩 2 个 keytab，无 cc 文件 ✓ |
| BE 状态 | `10002 Alive: true` ✓ |
| `SHOW CATALOGS` | `default_catalog` / `hive_catalog` / `hive_hivec` ✓ |
| `SELECT ... FROM hive_hivec.demo.users` | **5 行** ✓ |
| `SELECT ... FROM hive_catalog.default.test_tbl` | **2 行** ✓ |
| **跨集群 JOIN** | **5 行**（carol/alice/dave × arm_id 1,2）✓ |
| 跨集群 UNION ALL | `hive_c=5`、`arm=2` ✓ |
| BE 重启后复测 | 全部保持 ✓（非偶发） |

### 日志证据

```
be.out: [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=user_c@EXAMPLE.COM
be.out: [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=user_arm@HIVE_ARM.TEST
fe.out: [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=user_c@EXAMPLE.COM
fe.out: [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=user_arm@HIVE_ARM.TEST
```

四条各出现一次（按 `principal@@keytab` 缓存，不重复登录）。

## 并发验证

FE 侧 `doAsWithSwap` 去串行后的实测。

| 项目 | 结果 |
|---|---|
| 96 次并发元数据调用（16 并发 × 3 轮 × 2 catalog） | **3.34s** |
| 8 并发跨集群 UNION | **0.147s** |
| 压测中等待 UGI 全局锁的线程 | **0** |
| 压测中 BLOCKED 线程 | **0** |
| 3 轮交替查询稳定性 | 均 5/2，无抖动 |

线程栈用 jstack 在压测**进行中**抓取：

```bash
grep -c "waiting to lock.*UserGroupInformation" /tmp/stack.txt   # 0
grep -c "java.lang.Thread.State: BLOCKED" /tmp/stack.txt         # 0
```

去串行前，`synchronized(UserGroupInformation.class)` 会让所有 catalog 的
HMS 调用排队；现在两个 catalog 各持独立 UGI，完全并行。

## 历史日志干扰的排除

压测时 fe.out 里能搜到 `No service creds`，但经核实全部是**历史遗留** ——
位于 92232 行日志文件的第 81607 行，属于旧 jar 时期。

用打标记法确认零新增：

```bash
MARK="=== PROBE $(date +%s) ==="
echo "$MARK" >> fe.out
mysql -e "REFRESH EXTERNAL TABLE hive_catalog.default.test_tbl; SELECT ..."
sed -n "/$MARK/,\$p" fe.out | grep -i "error\|exception"   # 无输出
```

标记之后的日志显示正确获取了 `nn/hive-arm@HIVE_ARM.TEST` 服务票据。

**必须 `REFRESH EXTERNAL TABLE`**，否则走元数据缓存，根本不会访问 HMS/HDFS，
日志里什么都不会新增，容易误判为"没问题"。

## 早期验证（2026-07-16）

第一阶段成果，环境为已销毁的 `cluster_a`/`cluster_b`（realm `SR.TEST`）：

| 验证项 | 状态 |
|---|---|
| Kerberos HMS 认证（hive_a :9084 / hive_b :9085） | 通过 |
| HDFS Kerberos 认证（NameNode / DataNode） | 通过 |
| 跨 Catalog 元数据访问 | 通过 |
| HDFS HA 配置透传到 BE | 通过 |

**但当时的 Kerberos 隔离靠 BE 启动前 `kinit` + `KRB5CCNAME`**，
本质上仍是单一全局身份，两个 catalog 恰好用同一个 realm（`SR.TEST`）才能同时工作。
真正的跨 realm 场景直到 07-31 才解决。

## 已知限制

- `test_dml` 表（疑为 Hive ACID 表）`SHOW TABLES` 可见，但 `DESC` / `SELECT` 报表不存在
- Hive `count(*)` 默认读 metastore 统计信息，stats 过期时返回 0。
  需 `set hive.compute.query.using.stats=false` 或 `ANALYZE TABLE`
- 补丁只在 3.3.x 上验证过。3.4+ 需要 re-base，见 `patch_migration_assessment.md`

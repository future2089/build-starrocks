#!/bin/bash
# hotpatch_hadoop_ext.sh — 热更新 starrocks-hadoop-ext.jar 中的 HadoopExt 类
#
# 用途：
#   在不重新编译 FE/BE 的前提下，把本目录下的 HadoopExt.java 编译并替换进
#   已部署的 starrocks-hadoop-ext.jar，实现 per-catalog Kerberos 身份隔离。
#
# 背景（BE 侧 / getHDFSUGI）：
#   StarRocks 定制过的 org.apache.hadoop.fs.FileSystem.createFileSystem() 里有：
#       HadoopExt.getInstance().rewriteConfiguration(conf);
#       UserGroupInformation ugi = HadoopExt.getInstance().getHDFSUGI(conf);
#       return HadoopExt.getInstance().doAs(ugi, () -> ...真正创建 FS...);
#   社区版 getHDFSUGI() 是空实现返回 null，于是所有 catalog 共用 JVM 全局
#   loginUser（即默认 ticket cache），导致多个 Kerberos realm 互斥 ——
#   同一时刻只有一个安全 Hive 集群可访问。
#   本补丁实现 getHDFSUGI()，用 loginUserFromKeytabAndReturnUGI() 为每个
#   catalog 建立独立 UGI（不污染全局 loginUser）。
#
# 背景（FE 侧 / doAsWithSwap 快路径）：
#   HiveMetaClient.callRPC 用 doAsWithSwap(principal, keytab, action) 包装 HMS 调用。
#   旧实现是 synchronized(UserGroupInformation.class) + 全局 loginUserFromKeytab，
#   多 catalog 并发时元数据访问会串行。本补丁在 krb5ConfPath == null 时改走
#   缓存的独立 UGI（无全局锁、不改全局 loginUser），实现并行。
#   前提：单个 krb5.conf 内含所有 realm + 对应 [domain_realm] host 映射。
#
# 前置条件：
#   catalog 必须携带 hadoop.* 前缀的凭据属性（FE 的 toThrift 只透传
#   dfs./hadoop./ipc./hive. 前缀），例如：
#       "hadoop.security.authentication" = "kerberos"
#       "hadoop.kerberos.principal"      = "user_c@EXAMPLE.COM"
#       "hadoop.kerberos.keytab"         = "/opt/starrocks/krb5/user_c.keytab"
#   keytab 路径必须在 FE / BE 进程均可读。
#
# 用法（在 StarRocks 容器/主机内执行）：
#   bash hotpatch_hadoop_ext.sh            # 默认同时打 FE 与 BE 两个 jar
#   bash hotpatch_hadoop_ext.sh <jar路径>  # 只打指定 jar
#   执行后需重启对应的 FE / BE 生效。
#
# 注意：FE 与 BE 各有一份 starrocks-hadoop-ext.jar，位置不同，必须都更新：
#   FE: /opt/starrocks/fe/lib/starrocks-hadoop-ext.jar          (CLASSPATH 首位)
#   BE: /opt/starrocks/be/lib/jni-packages/starrocks-hadoop-ext.jar

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAMP=$(date +%Y%m%d%H%M)

: "${JAVA_HOME:=/usr/lib/jvm/java-11}"
export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"

FE_JAR=/opt/starrocks/fe/lib/starrocks-hadoop-ext.jar
BE_JAR=/opt/starrocks/be/lib/jni-packages/starrocks-hadoop-ext.jar

# HadoopExt.java 的权威副本在 patches/。允许三种放置方式：
#   1. 与本脚本同目录（把两个文件一起 docker cp 进容器时最常见）
#   2. 仓库布局 deploy/../patches/
#   3. 环境变量 HADOOP_EXT_SRC 显式指定
if [ -z "$HADOOP_EXT_SRC" ]; then
    for cand in "$SCRIPT_DIR/HadoopExt.java" "$SCRIPT_DIR/../patches/HadoopExt.java"; do
        [ -f "$cand" ] && { HADOOP_EXT_SRC="$cand"; break; }
    done
fi
[ -f "$HADOOP_EXT_SRC" ] || {
    echo "ERROR: 找不到 HadoopExt.java"
    echo "       已查找: $SCRIPT_DIR/HadoopExt.java"
    echo "               $SCRIPT_DIR/../patches/HadoopExt.java"
    echo "       或用 HADOOP_EXT_SRC=/path/to/HadoopExt.java 指定"
    exit 1
}
echo "=== 源文件: $HADOOP_EXT_SRC"

if [ -n "$1" ]; then
    TARGETS="$1"
else
    TARGETS=""
    [ -f "$FE_JAR" ] && TARGETS="$TARGETS $FE_JAR"
    [ -f "$BE_JAR" ] && TARGETS="$TARGETS $BE_JAR"
fi

[ -n "$TARGETS" ] || { echo "ERROR: 找不到任何 starrocks-hadoop-ext.jar"; exit 1; }

patch_one() {
    local JAR="$1"
    local ROLE_LIB
    # FE 依赖在 fe/lib/，BE 依赖在 be/lib/hadoop/common/
    case "$JAR" in
        */fe/lib/*) ROLE_LIB="/opt/starrocks/fe/lib/*" ;;
        *)          ROLE_LIB="/opt/starrocks/be/lib/hadoop/common/*" ;;
    esac
    local OUT
    OUT=$(mktemp -d)

    echo "=========================================================="
    echo "=== 目标 jar: $JAR"
    [ -f "$JAR" ] || { echo "ERROR: jar 不存在"; return 1; }

    echo "=== 备份"
    [ -f "${JAR}.orig" ] || cp -f "$JAR" "${JAR}.orig"
    cp -f "$JAR" "${JAR}.bak_${STAMP}"

    echo "=== 编译 HadoopExt.java (cp=$ROLE_LIB)"
    javac -nowarn -encoding UTF-8 \
          -cp "$JAR:$ROLE_LIB" \
          -d "$OUT" "$HADOOP_EXT_SRC"

    echo "=== 生成的 class"
    find "$OUT" -name '*.class' | sed "s|$OUT/||" | sort

    echo "=== 写回 jar"
    (cd "$OUT" && jar uf "$JAR" com/starrocks/connector/hadoop/)

    echo "=== 校验"
    local DUMP
    DUMP=$(javap -p -c -cp "$JAR:$ROLE_LIB" com.starrocks.connector.hadoop.HadoopExt 2>/dev/null)
    if echo "$DUMP" | grep -q "loginUserFromKeytabAndReturnUGI"; then
        echo "  [OK] 独立 UGI 登录逻辑已就位 (loginUserFromKeytabAndReturnUGI)"
    else
        echo "  [FAIL] 校验未通过，请回滚: cp ${JAR}.orig $JAR"
        rm -rf "$OUT"
        return 1
    fi
    if echo "$DUMP" | grep -q "getOrCreateKeytabUGI"; then
        echo "  [OK] doAsWithSwap 无锁快路径已就位 (getOrCreateKeytabUGI)"
    else
        echo "  [WARN] 未发现 getOrCreateKeytabUGI，FE 侧可能仍是串行版本"
    fi

    rm -rf "$OUT"
    echo "=== $JAR 完成"
}

for t in $TARGETS; do
    patch_one "$t"
done

echo
echo "=========================================================="
echo "全部完成。请重启 FE / BE 生效，并确认日志："
echo "  be.out : [hadoop-ext] created per-catalog HDFS UGI from keytab, principal=..."
echo "  fe.out : [hadoop-ext] created per-catalog HMS  UGI from keytab, principal=..."

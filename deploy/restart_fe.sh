#!/bin/bash
# restart_fe.sh — 重启 sr 容器内的 StarRocks FE
#
# 注意：容器 PID 1 不 reap 子进程，旧 FE 停止后可能留 <defunct>；
# 且残留的 fe.pid 会让 start_fe.sh 拒绝启动，必须先清掉。
# 严禁用 pkill -f StarRocksFE：模式串会匹配到 docker exec 自身命令行，
# 连带杀掉 exec 导致 ssh 直接以 255 退出。只能用精确 pid。

export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
export JAVA_HOME=/usr/lib/jvm/java-11
export PATH=$JAVA_HOME/bin:$PATH

OLD=$(cat /opt/starrocks/fe/bin/fe.pid 2>/dev/null)
echo "old FE pid=$OLD"
if [ -n "$OLD" ] && [ -d /proc/$OLD ]; then
  kill $OLD 2>/dev/null
  for i in $(seq 1 30); do
    [ -d /proc/$OLD ] || break
    st=$(awk '/^State/{print $2}' /proc/$OLD/status 2>/dev/null)
    [ "$st" = "Z" ] && break
    sleep 1
  done
  kill -9 $OLD 2>/dev/null
fi
sleep 2
rm -f /opt/starrocks/fe/bin/fe.pid

echo "########## 启动 FE ##########"
cd /opt/starrocks/fe
nohup ./bin/start_fe.sh --daemon > /tmp/fe_start.log 2>&1 < /dev/null &
disown

# FE 需要回放 image + 选主，等待时间比 BE 长
for i in $(seq 1 40); do
  sleep 3
  if mysql -h127.0.0.1 -P9030 -uroot -N -e "SELECT 1;" >/dev/null 2>&1; then
    echo "FE 已可接受连接（第 $((i*3)) 秒）"
    break
  fi
done

NEW=$(cat /opt/starrocks/fe/bin/fe.pid 2>/dev/null)
echo "new FE pid=$NEW"
echo "--- FE 角色 ---"
mysql -h127.0.0.1 -P9030 -uroot -e "SHOW FRONTENDS\G" 2>&1 | grep -E "Role|IsMaster|Alive|Join" | head -6

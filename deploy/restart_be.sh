#!/bin/bash
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH

OLD=$(cat /opt/starrocks/be/bin/be.pid 2>/dev/null)
echo "old pid=$OLD"
if [ -n "$OLD" ] && [ -d /proc/$OLD ]; then
  kill $OLD 2>/dev/null
  for i in $(seq 1 20); do
    [ -d /proc/$OLD ] || break
    st=$(awk '/^State/{print $2}' /proc/$OLD/status 2>/dev/null)
    [ "$st" = "Z" ] && break
    sleep 1
  done
  kill -9 $OLD 2>/dev/null
fi
sleep 2
rm -f /opt/starrocks/be/bin/be.pid

echo "########## 启动 BE ##########"
export JAVA_HOME=/usr/lib/jvm/java-11
cd /opt/starrocks/be
nohup ./bin/start_be.sh --daemon > /tmp/be_start.log 2>&1 < /dev/null &
disown
sleep 22
NEW=$(cat /opt/starrocks/be/bin/be.pid 2>/dev/null)
echo "new pid=$NEW"
if [ -n "$NEW" ] && [ -d /proc/$NEW ]; then
  awk '/^State/{print "State:",$2,$3}' /proc/$NEW/status
fi
echo "--- be.out tail ---"
tail -6 /opt/starrocks/be/log/be.out 2>&1

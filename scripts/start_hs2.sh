#!/bin/bash
export HADOOP_HOME=/opt/hadoop
export HIVE_HOME=/opt/hive
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)

pkill -f hiveserver2 2>/dev/null || true
sleep 2

kinit -kt /etc/security/keytabs/hive.service.keytab hive/hive-arm@HIVE_ARM.TEST
klist -5

nohup $HIVE_HOME/bin/hive --service hiveserver2 > /data/hive/logs/hs2.out 2>&1 &
echo "HS2_PID=$!"
sleep 8

echo "--- Port check ---"
ss -tlnp | grep -E ':10003 |:10005 '
echo "--- HS2 log tail ---"
tail -5 /data/hive/logs/hs2.out

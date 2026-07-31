#!/bin/bash
export HADOOP_HOME=/opt/hadoop
export HIVE_HOME=/opt/hive
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)

pkill -f "metastore" 2>/dev/null || true
pkill -f "hiveserver2" 2>/dev/null || true
sleep 2

kinit -kt /etc/security/keytabs/hive.service.keytab hive/hive-arm@HIVE_ARM.TEST

echo "Starting HMS on port 9086..."
nohup $HIVE_HOME/bin/hive --service metastore -p 9086 > /data/hive/logs/hms.out 2>&1 &
HMS_PID=$!
echo "HMS PID: $HMS_PID"
sleep 5

echo "Starting HS2 on port 10003..."
nohup $HIVE_HOME/bin/hive --service hiveserver2 > /data/hive/logs/hs2.out 2>&1 &
HS2_PID=$!
echo "HS2 PID: $HS2_PID"
sleep 5

echo "--- Hive Processes ---"
ps aux | grep -E "[m]etastore|[h]iveserver2" | grep -v grep
echo "--- Ports 9086 and 10003 ---"
ss -tlnp | grep -E "9086|10003"
echo "RESTART_DONE"

#!/bin/bash
set -e

MYSQL_DATADIR=/data/hive/mysql
HIVE_HOME=/opt/hive
HADOOP_HOME=/opt/hadoop
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk

# MySQL password for the hive_arm user - supply via environment, never hardcode.
#   export HIVE_DB_PASSWORD='...'
HIVE_DB_PASSWORD="${HIVE_DB_PASSWORD:?set HIVE_DB_PASSWORD before running}"

echo "=== Step 1: MySQL init ==="
mkdir -p /data/hive/mysql /var/run/mysqld /var/log/mysql
mysqld --initialize-insecure --user=root --datadir=$MYSQL_DATADIR 2>&1 | tail -3
echo "MySQL initialized"

echo "=== Step 2: Start MySQL ==="
/usr/sbin/mysqld --datadir=$MYSQL_DATADIR --socket=/var/lib/mysql/mysql.sock \
  --pid-file=/var/run/mysqld/mysqld.pid --user=root &
sleep 5
mysql -u root -e "SELECT 1 AS test" && echo "MySQL running"

echo "=== Step 3: Create Hive DB ==="
mysql -u root -e "CREATE DATABASE IF NOT EXISTS hive_arm DEFAULT CHARACTER SET utf8;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'hive_arm'@'localhost' IDENTIFIED BY '$HIVE_DB_PASSWORD';"
mysql -u root -e "GRANT ALL PRIVILEGES ON hive_arm.* TO 'hive_arm'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"
echo "DB created"

echo "=== Step 4: Copy Hive configs ==="
mkdir -p $HIVE_HOME/conf /data/hive/logs
echo "Configs will be copied via docker cp"

echo "=== Step 5: Find MySQL JDBC ==="
MYSQL_JAR=$(find / -name 'mysql-connector-java*.jar' -type f 2>/dev/null | head -1)
if [ -n "$MYSQL_JAR" ]; then
  cp $MYSQL_JAR $HIVE_HOME/lib/
  echo "Found JDBC: $MYSQL_JAR"
else
  echo "WARNING: MySQL JDBC not found"
fi

echo "=== Step 6: Init Hive schema ==="
export HADOOP_HOME=$HADOOP_HOME
export JAVA_HOME=$JAVA_HOME
export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)
HADOOP_CLASSPATH=$HADOOP_CLASSPATH $HIVE_HOME/bin/schematool -dbType mysql -initSchema 2>&1 | tail -10
echo "Schema init OK"

echo "=== Step 7: kinit for Hive ==="
kinit -kt /etc/security/keytabs/hive.service.keytab hive/hive-arm@HIVE_ARM.TEST
echo "kinit OK"

echo "=== Step 8: Start HMS ==="
export HADOOP_HOME=$HADOOP_HOME
export JAVA_HOME=$JAVA_HOME
export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)
nohup $HIVE_HOME/bin/hive --service metastore -p 9086 > /data/hive/logs/hms.out 2>&1 &
echo "HMS started, PID: $!"
sleep 5

echo "=== Step 9: Start HS2 ==="
nohup $HIVE_HOME/bin/hive --service hiveserver2 > /data/hive/logs/hs2.out 2>&1 &
echo "HS2 started, PID: $!"
sleep 5

echo "=== Step 10: Check processes ==="
ps aux | grep -E "[m]etastore|[h]iveserver2" | awk '{print $11}' 2>/dev/null || echo "not found"
echo "DONE"

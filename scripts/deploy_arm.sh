#!/bin/bash
set -e

HOST_181="root@192.168.0.181"

run() {
    echo ">>> $*"
    ssh "$HOST_181" "$@"
    echo ""
}

run docker exec hadoop-arm echo "--- Container OK ---"

JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.462.b08-4.oe2403sp2.aarch64
HADOOP_HOME=/data/package/hadoop-3.3.6
HIVE_HOME=/data/package/apache-hive-3.1.3-bin

# Verify Java
run docker exec hadoop-arm java -version

# Copy KDC config + keytabs
run docker cp /etc/krb5.conf hadoop-arm:/etc/krb5.conf
run docker cp /etc/hdfs.keytab hadoop-arm:/etc/hdfs.keytab
run docker cp /etc/hive.keytab hadoop-arm:/etc/hive.keytab

# Check Hadoop
run docker exec hadoop-arm ls -la "$HADOOP_HOME/bin/hdfs"

# Run hdfs version
run docker exec hadoop-arm env JAVA_HOME="$JAVA_HOME" "$HADOOP_HOME/bin/hdfs" version

echo "=== Container READY ==="

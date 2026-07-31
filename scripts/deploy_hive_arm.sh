#!/bin/bash
# =============================================================
# deploy_hive_arm.sh
# Deploy all-in-one container on 192.168.0.181 (ARM64):
# KDC + HDFS (pseudo HA, hacluster) + Hive (HMS 9086 + HS2 10003)
# Realm: HIVE_ARM.TEST
# Uses --network host with non-standard ports to avoid conflicts
# =============================================================
set -euo pipefail

HOST="root@192.168.0.181"
HOST_IP="192.168.0.181"
CONTAINER="hive_arm"
REALM="HIVE_ARM.TEST"
HADOOP_HOME="/opt/hadoop"
HIVE_HOME="/opt/hive"
JAVA_HOME="/usr/lib/jvm/java-1.8.0-openjdk"
KEYTAB_DIR="/etc/security/keytabs"
LOCAL_CFG="/tmp/hive_arm_configs"

# -------------------------------------------------------------------
# Credentials MUST come from the environment - never hardcode them here.
#   export KDC_MASTER_PASSWORD='...'   # KDC database master password
#   export KRB_USER_PASSWORD='...'     # password of the user_arm principal
#   export HIVE_DB_PASSWORD='...'      # MySQL password of the hive_arm user
# -------------------------------------------------------------------
KDC_MASTER_PASSWORD="${KDC_MASTER_PASSWORD:?set KDC_MASTER_PASSWORD before running}"
KRB_USER_PASSWORD="${KRB_USER_PASSWORD:?set KRB_USER_PASSWORD before running}"
HIVE_DB_PASSWORD="${HIVE_DB_PASSWORD:?set HIVE_DB_PASSWORD before running}"

# Run command on host
run_host() { echo ">>> [HOST] $*"; ssh "$HOST" "$@"; }

# Run command inside container (no bash -c wrapper, passes args directly)
run_cont() { echo ">>> [CONT] $*"; ssh "$HOST" docker exec "$CONTAINER" "$@"; }

# Run command in shell inside container (for pipes, redirects, env vars)
run_cont_sh() { echo ">>> [CONT] $*"; ssh "$HOST" "docker exec $CONTAINER bash -c $(printf '%q' "$*")"; }

step1_container() {
    echo "=== Step 1: Start container ==="
    run_host "docker rm -f $CONTAINER 2>/dev/null || true"
    run_host docker run -d --name "$CONTAINER" \
        --hostname hive-arm \
        --network host \
        -v /Bigdata2/data/package/hadoop-3.3.6:/opt/hadoop \
        -v /Bigdata2/data/package/apache-hive-3.1.3-bin:/opt/hive \
        openeuler/openeuler:24.03 sleep infinity
    sleep 3
    run_cont echo READY
}

step2_install() {
    echo "=== Step 2: Install packages ==="
    run_cont sh -c "dnf install -y java-1.8.0-openjdk-headless java-1.8.0-openjdk-devel krb5-server krb5-workstation mysql-server procps-ng openssh-clients 2>&1 | tail -3"
    run_cont java -version
}

prepare_configs() {
    rm -rf "$LOCAL_CFG"; mkdir -p "$LOCAL_CFG"

    cat > "$LOCAL_CFG/kdc.conf" << 'EOF'
[kdcdefaults]
 kdc_ports = 8888
 kdc_tcp_ports = 8888

[realms]
 HIVE_ARM.TEST = {
  master_key_type = aes256-cts
  acl_file = /var/kerberos/krb5kdc/kadm5.acl
  dict_file = /usr/share/dict/words
  admin_keytab = /var/kerberos/krb5kdc/kadm5.keytab
  max_renewable_life = 7d
  supported_enctypes = aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal
 }
EOF

    echo '*/admin@HIVE_ARM.TEST *' > "$LOCAL_CFG/kadm5.acl"

    cat > "$LOCAL_CFG/krb5.conf" << 'EOF'
[logging]
 default = FILE:/var/log/krb5libs.log
 kdc = FILE:/var/log/krb5kdc.log
 admin_server = FILE:/var/log/kadmind.log

[libdefaults]
 dns_lookup_realm = false
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true
 rdns = false
 default_realm = HIVE_ARM.TEST
 default_ccache_name = FILE:/tmp/krb5cc_%{uid}

[realms]
 HIVE_ARM.TEST = {
  kdc = 192.168.0.181:8888
  admin_server = 192.168.0.181:7490
  default_domain = hive-arm
 }

[domain_realm]
 .hive-arm = HIVE_ARM.TEST
 hive-arm = HIVE_ARM.TEST
EOF

    cat > "$LOCAL_CFG/core-site.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property><name>fs.defaultFS</name><value>hdfs://hacluster</value></property>
  <property><name>hadoop.tmp.dir</name><value>/tmp/hadoop</value></property>
  <property><name>hadoop.security.authentication</name><value>kerberos</value></property>
  <property><name>hadoop.security.authorization</name><value>true</value></property>
  <property><name>ipc.client.fallback-to-simple-auth-allowed</name><value>true</value></property>
  <property><name>hadoop.proxyuser.root.hosts</name><value>*</value></property>
  <property><name>hadoop.proxyuser.root.groups</name><value>*</value></property>
</configuration>
EOF

    cat > "$LOCAL_CFG/hdfs-site.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property><name>dfs.replication</name><value>1</value></property>
  <property><name>dfs.namenode.name.dir</name><value>/data/hadoop/name</value></property>
  <property><name>dfs.datanode.data.dir</name><value>/data/hadoop/data</value></property>
  <property><name>dfs.datanode.hostname</name><value>$HOST_IP</value></property>
  <property><name>dfs.datanode.address</name><value>0.0.0.0:9866</value></property>
  <property><name>dfs.datanode.http.address</name><value>0.0.0.0:9864</value></property>
  <property><name>dfs.permissions</name><value>false</value></property>
  <property><name>dfs.nameservices</name><value>hacluster</value></property>
  <property><name>dfs.ha.namenodes.hacluster</name><value>nn1</value></property>
  <property><name>dfs.namenode.rpc-address.hacluster.nn1</name><value>0.0.0.0:8021</value></property>
  <property><name>dfs.namenode.http-address.hacluster.nn1</name><value>0.0.0.0:50071</value></property>
  <property><name>dfs.client.failover.proxy.provider.hacluster</name><value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value></property>
  <property><name>dfs.namenode.keytab.file</name><value>$KEYTAB_DIR/nn.service.keytab</value></property>
  <property><name>dfs.namenode.kerberos.principal</name><value>nn/hive-arm@$REALM</value></property>
  <property><name>dfs.datanode.keytab.file</name><value>$KEYTAB_DIR/dn.service.keytab</value></property>
  <property><name>dfs.datanode.kerberos.principal</name><value>dn/hive-arm@$REALM</value></property>
  <property><name>dfs.data.transfer.protection</name><value>authentication</value></property>
  <property><name>dfs.block.access.token.enable</name><value>true</value></property>
  <property><name>ignore.secure.ports.for.testing</name><value>true</value></property>
</configuration>
EOF

    cat > "$LOCAL_CFG/hive-site.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property><name>javax.jdo.option.ConnectionURL</name><value>jdbc:mysql://127.0.0.1:3306/hive_arm?createDatabaseIfNotExist=true\&amp;useSSL=false\&amp;serverTimezone=UTC</value></property>
  <property><name>javax.jdo.option.ConnectionDriverName</name><value>com.mysql.jdbc.Driver</value></property>
  <property><name>javax.jdo.option.ConnectionUserName</name><value>hive_arm</value></property>
  <property><name>javax.jdo.option.ConnectionPassword</name><value>$HIVE_DB_PASSWORD</value></property>
  <property><name>datanucleus.autoCreateSchema</name><value>true</value></property>
  <property><name>datanucleus.fixedDatastore</name><value>false</value></property>
  <property><name>datanucleus.autoCreateTables</name><value>true</value></property>
  <property><name>datanucleus.schema.autoCreateAll</name><value>true</value></property>
  <property><name>hive.metastore.uris</name><value>thrift://0.0.0.0:9086</value></property>
  <property><name>hive.metastore.sasl.enabled</name><value>true</value></property>
  <property><name>hive.metastore.kerberos.principal</name><value>hive/hive-arm@$REALM</value></property>
  <property><name>hive.metastore.kerberos.keytab.file</name><value>$KEYTAB_DIR/hive.service.keytab</value></property>
  <property><name>hive.metastore.warehouse.dir</name><value>/user/hive/warehouse</value></property>
  <property><name>hive.server2.thrift.port</name><value>10003</value></property>
  <property><name>hive.server2.thrift.bind.host</name><value>0.0.0.0</value></property>
  <property><name>hive.server2.authentication</name><value>KERBEROS</value></property>
  <property><name>hive.server2.authentication.kerberos.principal</name><value>hive/hive-arm@$REALM</value></property>
  <property><name>hive.server2.authentication.kerberos.keytab</name><value>$KEYTAB_DIR/hive.service.keytab</value></property>
  <property><name>hive.server2.enable.doAs</name><value>false</value></property>
  <property><name>hive.server2.support.dynamic.service.discovery</name><value>false</value></property>
  <property><name>hive.exec.scratchdir</name><value>/tmp/hive</value></property>
  <property><name>hive.metastore.schema.verification</name><value>false</value></property>
  <property><name>hive.metastore.event.db.notification.api.auth</name><value>false</value></property>
</configuration>
EOF

    cat > "$LOCAL_CFG/hive_jaas.conf" << 'EOF'
HiveServer2 {
  com.sun.security.auth.module.Krb5LoginModule required
  useKeyTab=true
  keyTab="/etc/security/keytabs/hive.service.keytab"
  principal="hive/hive-arm@HIVE_ARM.TEST"
  storeKey=true
  useTicketCache=false;
};
Client {
  com.sun.security.auth.module.Krb5LoginModule required
  useKeyTab=true
  keyTab="/etc/security/keytabs/hive.service.keytab"
  principal="hive/hive-arm@HIVE_ARM.TEST"
  storeKey=true
  useTicketCache=false;
};
EOF
    echo "Config files ready"
}

step3_kdc() {
    echo "=== Step 3: Deploy KDC ==="
    run_cont mkdir -p /var/kerberos/krb5kdc "$KEYTAB_DIR" /data/logs
    run_host docker cp "$LOCAL_CFG/kdc.conf" "$CONTAINER":/var/kerberos/krb5kdc/kdc.conf
    run_host docker cp "$LOCAL_CFG/kadm5.acl" "$CONTAINER":/var/kerberos/krb5kdc/kadm5.acl
    run_host docker cp "$LOCAL_CFG/krb5.conf" "$CONTAINER":/etc/krb5.conf

    run_cont sh -c "echo '$KDC_MASTER_PASSWORD' | kdb5_util create -s -r $REALM -P '$KDC_MASTER_PASSWORD'"

    # Write kadmin commands to a script to avoid quoting issues
    run_cont sh -c "kadmin.local -q 'addprinc -randkey nn/hive-arm@$REALM'"
    run_cont sh -c "kadmin.local -q 'addprinc -randkey dn/hive-arm@$REALM'"
    run_cont sh -c "kadmin.local -q 'addprinc -randkey hive/hive-arm@$REALM'"
    run_cont sh -c "kadmin.local -q 'addprinc -pw $KRB_USER_PASSWORD user_arm@$REALM'"

    run_cont sh -c "kadmin.local -q 'ktadd -k $KEYTAB_DIR/nn.service.keytab nn/hive-arm@$REALM'"
    run_cont sh -c "kadmin.local -q 'ktadd -k $KEYTAB_DIR/dn.service.keytab dn/hive-arm@$REALM'"
    run_cont sh -c "kadmin.local -q 'ktadd -k $KEYTAB_DIR/hive.service.keytab hive/hive-arm@$REALM'"
    run_cont sh -c "kadmin.local -q 'ktadd -k $KEYTAB_DIR/user_arm.keytab user_arm@$REALM'"

    run_cont chmod 644 "$KEYTAB_DIR"/*.keytab || true

    # Start KDC
    run_cont krb5kdc
    run_cont kadmind
    sleep 2

    # Verify
    run_cont sh -c "KRB5CCNAME=FILE:/tmp/krb5cc_v kinit -kt $KEYTAB_DIR/nn.service.keytab nn/hive-arm@$REALM && klist && kdestroy"
}

step4_hdfs() {
    echo "=== Step 4: HDFS ==="
    run_cont mkdir -p /data/hadoop/name /data/hadoop/data /data/logs
    run_host docker cp "$LOCAL_CFG/core-site.xml" "$CONTAINER":"$HADOOP_HOME"/etc/hadoop/core-site.xml
    run_host docker cp "$LOCAL_CFG/hdfs-site.xml" "$CONTAINER":"$HADOOP_HOME"/etc/hadoop/hdfs-site.xml

    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME && $HADOOP_HOME/bin/hdfs namenode -format -force 2>&1 | tail -5"
    echo "Format OK"

    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME HADOOP_LOG_DIR=/data/logs && kinit -kt $KEYTAB_DIR/nn.service.keytab nn/hive-arm@$REALM && $HADOOP_HOME/bin/hdfs --daemon start namenode 2>&1"
    sleep 3
    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME HADOOP_LOG_DIR=/data/logs && kinit -kt $KEYTAB_DIR/dn.service.keytab dn/hive-arm@$REALM && $HADOOP_HOME/bin/hdfs --daemon start datanode 2>&1"
    sleep 3

    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME && kinit -kt $KEYTAB_DIR/nn.service.keytab nn/hive-arm@$REALM && $HADOOP_HOME/bin/hdfs dfsadmin -report 2>&1 | head -15"
}

step5_mysql() {
    echo "=== Step 5: MySQL ==="
    run_cont mkdir -p /data/hive/mysql
    run_cont sh -c "mysqld --initialize-insecure --user=root --datadir=/data/hive/mysql 2>&1 | tail -3 || true"
    run_cont sh -c "mysqld_safe --datadir=/data/hive/mysql --user=root &"
    sleep 4
    run_cont mysql -u root -e "CREATE DATABASE IF NOT EXISTS hive_arm DEFAULT CHARACTER SET utf8; CREATE USER IF NOT EXISTS 'hive_arm'@'localhost' IDENTIFIED BY '$HIVE_DB_PASSWORD'; GRANT ALL PRIVILEGES ON hive_arm.* TO 'hive_arm'@'localhost'; FLUSH PRIVILEGES;"
    echo "MySQL OK"
}

step6_hive() {
    echo "=== Step 6: Hive ==="
    run_cont mkdir -p "$HIVE_HOME/conf" /data/hive/logs
    run_host docker cp "$LOCAL_CFG/hive-site.xml" "$CONTAINER":"$HIVE_HOME/conf/hive-site.xml"
    run_host docker cp "$LOCAL_CFG/hive_jaas.conf" "$CONTAINER":"$HIVE_HOME/conf/hive_jaas.conf"

    # Find MySQL JDBC driver
    run_cont sh -c "MYSQL_JAR=\$(find / -name 'mysql-connector-java*.jar' -type f 2>/dev/null | head -1); if [ -n \"\$MYSQL_JAR\" ]; then cp \$MYSQL_JAR $HIVE_HOME/lib/ && echo \"FOUND \$MYSQL_JAR\"; else echo 'MYSQL_JAR_NOT_FOUND'; fi"

    # Schema init
    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME && HADOOP_CLASSPATH=\$($HADOOP_HOME/bin/hadoop classpath) $HIVE_HOME/bin/schematool -dbType mysql -initSchema 2>&1 | tail -10"
    echo "Schema init OK"

    # Start HMS
    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME HADOOP_OPTS='-Djava.security.krb5.conf=/etc/krb5.conf -Djava.security.auth.login.config=$HIVE_HOME/conf/hive_jaas.conf' && kinit -kt $KEYTAB_DIR/hive.service.keytab hive/hive-arm@$REALM && nohup $HIVE_HOME/bin/hive --service metastore -p 9086 > /data/hive/logs/hms.out 2>&1 &"
    sleep 5

    # Start HS2
    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME && nohup $HIVE_HOME/bin/hive --service hiveserver2 > /data/hive/logs/hs2.out 2>&1 &"
    sleep 5

    run_cont sh -c "ps aux | grep -E '[m]etastore|[h]iveserver2' | grep -v grep"
}

step7_verify() {
    echo "=== Step 7: Verify ==="
    echo "--- Processes ---"
    run_cont sh -c "ps aux | grep -E '[n]amenode|[d]atanode|[m]etastore|[h]iveserver2|[k]rb5kdc|[m]ysqld' | grep -v grep | awk '{print \$11,\$12,\$13}'"

    echo "--- Ports ---"
    run_cont sh -c "ss -tlnp | grep -E ':8888 |:7490 |:8021 |:50071 |:9866 |:9864 |:9086 |:10003 |:3306 '"

    echo "--- HDFS test with user_arm ---"
    run_cont sh -c "export HADOOP_HOME=$HADOOP_HOME JAVA_HOME=$JAVA_HOME && KRB5CCNAME=FILE:/tmp/krb5cc_u kinit -kt $KEYTAB_DIR/user_arm.keytab user_arm@$REALM && KRB5CCNAME=FILE:/tmp/krb5cc_u $HADOOP_HOME/bin/hdfs dfs -ls hdfs://hacluster/"

    echo ""
    echo "======================================"
    echo "  DEPLOYMENT COMPLETE"
    echo "======================================"
    echo ""
    echo "Endpoints (external via $HOST_IP):"
    echo "  KDC:          $HOST_IP:8888"
    echo "  HDFS NN RPC:  $HOST_IP:8021"
    echo "  HDFS NN HTTP: $HOST_IP:50071"
    echo "  HDFS DN:      $HOST_IP:9866"
    echo "  Hive HMS:     $HOST_IP:9086"
    echo "  Hive HS2:     $HOST_IP:10003"
    echo ""
    echo "Principals @ $REALM:"
    echo "  nn/hive-arm     keytab: nn.service.keytab"
    echo "  dn/hive-arm     keytab: dn.service.keytab"
    echo "  hive/hive-arm   keytab: hive.service.keytab"
    echo "  user_arm        keytab: user_arm.keytab / pwd: \$KRB_USER_PASSWORD"
}

# Main
prepare_configs
step1_container
step2_install
step3_kdc
step4_hdfs
step5_mysql
step6_hive
step7_verify
rm -rf "$LOCAL_CFG"

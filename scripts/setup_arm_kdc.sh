#!/bin/bash
# Setup KDC container on 192.168.0.181 for ARM.SR.TEST realm

set -e

KDC_IMAGE="openeuler/openeuler:22.03"
KDC_CONTAINER="kdc-arm"
KRB5_CONF="/etc/krb5.conf"

# Start container if not running
docker rm -f $KDC_CONTAINER 2>/dev/null || true
docker run -d --name $KDC_CONTAINER --network host --restart unless-stopped $KDC_IMAGE sleep infinity

# Install packages
docker exec $KDC_CONTAINER dnf install -y krb5-server krb5-workstation krb5-libs

# Configure krb5.conf
cat > /tmp/krb5_arm.conf << 'KRBCONF'
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
 default_realm = ARM.SR.TEST
 default_ccache_name = FILE:/tmp/krb5cc_%{uid}

[realms]
 ARM.SR.TEST = {
  kdc = 192.168.0.181:88
  admin_server = 192.168.0.181:749
  default_domain = arm.sr.test
 }

[domain_realm]
 .arm.sr.test = ARM.SR.TEST
 arm.sr.test = ARM.SR.TEST
KRBCONF

docker cp /tmp/krb5_arm.conf $KDC_CONTAINER:$KRB5_CONF

# Create KDC database
docker exec $KDC_CONTAINER bash -c "printf 'Thinker@123\nThinker@123\n' | kdb5_util create -s -r ARM.SR.TEST"

# Add principals
docker exec $KDC_CONTAINER kadmin.local -q "addprinc -randkey hdfs/arm-ha@ARM.SR.TEST"
docker exec $KDC_CONTAINER kadmin.local -q "addprinc -randkey hive/arm-hive@ARM.SR.TEST"

# Export keytabs
mkdir -p /data/keytabs
docker exec $KDC_CONTAINER kadmin.local -q "ktadd -k /tmp/hdfs.keytab hdfs/arm-ha@ARM.SR.TEST"
docker exec $KDC_CONTAINER kadmin.local -q "ktadd -k /tmp/hive.keytab hive/arm-hive@ARM.SR.TEST"
docker cp $KDC_CONTAINER:/tmp/hdfs.keytab /data/keytabs/hdfs.keytab
docker cp $KDC_CONTAINER:/tmp/hive.keytab /data/keytabs/hive.keytab

# Start KDC services
docker exec -d $KDC_CONTAINER /usr/sbin/krb5kdc
docker exec -d $KDC_CONTAINER /usr/sbin/kadmind

echo "KDC container setup complete"
echo "Principals: hdfs/arm-ha@ARM.SR.TEST, hive/arm-hive@ARM.SR.TEST"
echo "Keytabs: /data/keytabs/hdfs.keytab, /data/keytabs/hive.keytab"

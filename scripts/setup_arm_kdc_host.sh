#!/bin/bash
set -e

# Stop any existing KDC processes
killall krb5kdc kadmind 2>/dev/null || true
rm -f /var/kerberos/krb5kdc/principal* /var/kerberos/krb5kdc/.k5.ARM.SR.TEST

# Setup krb5.conf
cp /tmp/krb5_kdc.conf /etc/krb5.conf

# Setup kdc.conf
cp /tmp/kdc_arm.conf /var/kerberos/krb5kdc/kdc.conf

# Create KDC database
echo "Thinker@123" | kdb5_util create -s -r ARM.SR.TEST -P Thinker@123

# Add principals
kadmin.local -q "addprinc -randkey hdfs/arm-ha@ARM.SR.TEST"
kadmin.local -q "addprinc -randkey hive/arm-hive@ARM.SR.TEST"

# Export keytabs
kadmin.local -q "ktadd -k /etc/hdfs.keytab hdfs/arm-ha@ARM.SR.TEST"
kadmin.local -q "ktadd -k /etc/hive.keytab hive/arm-hive@ARM.SR.TEST"

# Start KDC services
krb5kdc
kadmind

# Verify
KRB5CCNAME=FILE:/tmp/krb5cc_test /usr/bin/kinit -kt /etc/hdfs.keytab hdfs/arm-ha@ARM.SR.TEST
KRB5CCNAME=FILE:/tmp/krb5cc_test /usr/bin/klist

echo "=== KDC Setup Complete ==="
echo "Principals: hdfs/arm-ha, hive/arm-hive"
echo "Keytabs: /etc/hdfs.keytab, /etc/hive.keytab"

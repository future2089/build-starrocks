#!/usr/bin/env bash
# BE startup wrapper with Kerberos kinit
# Place at: $STARROCKS_HOME/be/bin/start_be.sh
# Keytab at: /etc/be.keytab (copy from host's hdfs.nn.keytab)

curdir=`dirname "$0"`
curdir=`cd "$curdir"; pwd`
export STARROCKS_HOME=`cd "$curdir/.."; pwd`

# Kerberos credential cache for BE's HDFS client
export KRB5CCNAME=FILE:/tmp/krb5cc_be

# Obtain Kerberos TGT before starting BE
kinit -kt /etc/be.keytab hdfs/cluster_a@SR.TEST

exec ${STARROCKS_HOME}/bin/start_backend.sh --be "$@"

#!/bin/bash
cat >> /opt/hadoop/etc/hadoop/core-site.xml << 'EOF'
<property><name>hadoop.proxyuser.hive.hosts</name><value>*</value></property>
<property><name>hadoop.proxyuser.hive.groups</name><value>*</value></property>
</configuration>
EOF
grep proxyuser.hive /opt/hadoop/etc/hadoop/core-site.xml

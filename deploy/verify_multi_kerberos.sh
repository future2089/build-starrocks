#!/bin/bash
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH

echo "########## A. 当前系统 ticket cache（期望：无）##########"
ls -l /tmp/krb5cc_* 2>&1 | head -3
ls -l /opt/starrocks/krb5/ 2>&1

echo
echo "########## B. BE 存活 ##########"
mysql -h127.0.0.1 -P9030 -uroot -e "SHOW BACKENDS\G" 2>&1 | grep -E "BackendId|Alive|LastStartTime" | head -4

echo
echo "########## C. Catalog 列表 ##########"
mysql -h127.0.0.1 -P9030 -uroot -e "SHOW CATALOGS;" 2>&1 | head -6

echo
echo "########## D. 双集群并发查询 ##########"
mysql -h127.0.0.1 -P9030 -uroot -e "
SELECT 'hive_c(EXAMPLE.COM)' AS cluster, count(*) AS cnt FROM hive_hivec.demo.users
UNION ALL
SELECT 'arm(HIVE_ARM.TEST)', count(*) FROM hive_catalog.\`default\`.test_tbl;" 2>&1 | head -8

echo
echo "########## E. 跨集群 JOIN ##########"
mysql -h127.0.0.1 -P9030 -uroot -e "
SELECT a.id, a.name, b.id AS arm_id
FROM hive_hivec.demo.users a
JOIN hive_catalog.\`default\`.test_tbl b ON 1=1
LIMIT 5;" 2>&1 | head -10

echo
echo "########## F. per-catalog UGI 日志 ##########"
grep -a "created per-catalog HDFS UGI" /opt/starrocks/be/log/be.out 2>/dev/null | tail -6

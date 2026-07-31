# configs/ — StarRocks per-catalog Kerberos + HA Hive configuration

## Layout (after 2026-07-30 cleanup)

```
configs/
├── README.md                 # this file
├── archive/                  # 204 one-off POC/debugging scripts (see archive/MANIFEST.md)
│   └── MANIFEST.md           # full list + prefix breakdown of archived scripts
├── be/                       # BE-side config (be.conf, core-site.xml, hdfs-site.xml, jaas.conf, supervisord.conf)
├── cluster_a/                # Cluster A Hive/HDFS config fragments
├── cluster_b/                # Cluster B Hive/HDFS config fragments
├── host/                     # host-level krb5 / hadoop config
├── kdc/                      # KDC config (kdc.conf, kadm5.acl, krb5.conf)
├── arm-hdfs-site*.xml        # ARM HDFS site configs (v1/v2/v3 iterations)
├── arm-hive-site-derby.xml   # ARM Hive Derby metastore config
├── arm-krb5.conf             # ARM realm krb5
├── krb5_arm.conf             # ARM krb5 (variant)
├── krb5_arm_per_catalog.conf # ARM per-catalog krb5
├── krb5_kdc.conf             # KDC krb5
├── kdc_arm.conf              # ARM KDC config
├── starrocks-arm.keytab      # ARM service keytab
├── starrocks-arm-keytab.b64  # ARM service keytab (base64)
├── starrocks-arm-v2.b64      # ARM service keytab v2 (base64)
├── create_arm_catalog.sql    # ARM catalog DDL
└── TestKrb.java              # standalone Kerberos test (kept at root)
```

## Note

The 204 scripts previously at the root (`check_*`, `test_*`, `fix_*`, `verify_*`,
`debug_*`, ... ) were exploratory debugging artifacts. They were NOT deleted —
they live in `archive/` with a manifest, so any diagnosis can be reproduced.

Reusable ops/config-generation scripts should be promoted out of `archive/` into
`scripts/` (the canonical deployment dir) rather than left at the root.

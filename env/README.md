# env/ — 环境配置与集群资料

测试环境的配置文件、keytab、krb5.conf 等。按集群归置。

```
env/
├── configs/     StarRocks BE/FE 与各 Hive 集群的配置片段、KDC 配置、keytab
│   ├── be/          BE 侧 be.conf / core-site.xml / hdfs-site.xml / jaas.conf
│   ├── host/        宿主机 krb5 / hadoop 配置
│   ├── kdc/         KDC 的 kdc.conf / kadm5.acl / krb5.conf
│   ├── cluster_a/   已销毁环境的遗留片段（仅留档）
│   ├── cluster_b/   同上
│   ├── archive/     204 个一次性 POC 脚本，见其中 MANIFEST.md
│   └── arm-*.xml, krb5_*.conf, *.keytab ...
└── arm/         ARM (192.168.0.181) 鲲鹏平台构建与 Hive 集群资料
    ├── BUILD_RESULT.md    ARM64 编译结果
    ├── build_arm*.sh      ARM 构建脚本
    └── conf/              hive_arm 容器内已生效的 yarn-site / mapred-site
```

## 几个要点

**`env/arm/conf/` 里的两个 xml 是真实生效的修复。**
`hive_arm` 容器内原本 `yarn-site.xml` 是空模板，导致本地 Hive 查询失败。
补上 `yarn.resourcemanager.principal=yarn/hive-arm@HIVE_ARM.TEST` 与
`mapreduce.framework.name=local` 后才通。改动留档在此。

**`configs/cluster_a/` 和 `cluster_b/` 是历史遗留。**
对应已销毁的 POC 容器（realm `SR.TEST`），仅供追溯，不要用。
当前拓扑见主 README 第 3 节。

**keytab 文件不要提交到公开仓库。**
`configs/` 下有 `starrocks-arm.keytab` 及其 base64 副本。
这些是测试环境凭据，若仓库要外发，先清理。

**BE/FE 的 `core-site.xml` 里 `hadoop.security.auth_to_local` 必须含所有 realm 的 RULE**，
否则会报 `KerberosName$NoMatchingRule`。见 `configs/be/core-site.xml`。

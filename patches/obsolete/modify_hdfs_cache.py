import re

with open('/data/starrocks-build/starrocks-3.3.17/be/src/fs/hdfs/hdfs_fs_cache.cpp', 'r') as f:
    content = f.read()

old = """    // Set for hdfs client hedged read
    std::string hedged_read_threadpool_size = std::to_string(config::hdfs_client_hedged_read_threadpool_size);
    std::string hedged_read_threshold_millis = std::to_string(config::hdfs_client_hedged_read_threshold_millis);
    if (config::hdfs_client_enable_hedged_read) {
        hdfsBuilderConfSetStr(hdfs_builder, "dfs.client.hedged.read.threadpool.size",
                              hedged_read_threadpool_size.data());
        hdfsBuilderConfSetStr(hdfs_builder, "dfs.client.hedged.read.threshold.millis",
                              hedged_read_threshold_millis.data());
    }

    hdfs_client->hdfs_fs = hdfsBuilderConnect(hdfs_builder);
    if (hdfs_client->hdfs_fs == nullptr) {
        return Status::InternalError(strings::Substitute("fail to connect hdfs namenode, namenode=$0, err=$1", namenode,
                                                         get_hdfs_err_msg()));
    }
    return Status::OK();
}"""

new = """    // Set for hdfs client hedged read
    std::string hedged_read_threadpool_size = std::to_string(config::hdfs_client_hedged_read_threadpool_size);
    std::string hedged_read_threshold_millis = std::to_string(config::hdfs_client_hedged_read_threshold_millis);
    if (config::hdfs_client_enable_hedged_read) {
        hdfsBuilderConfSetStr(hdfs_builder, "dfs.client.hedged.read.threadpool.size",
                              hedged_read_threadpool_size.data());
        hdfsBuilderConfSetStr(hdfs_builder, "dfs.client.hedged.read.threshold.millis",
                              hedged_read_threshold_millis.data());
    }

    // Per-catalog Kerberos authentication support.
    // If the catalog specifies hadoop.security.authentication=kerberos with
    // keytab and principal, set up per-connection credential cache so that
    // different catalogs can use different Kerberos identities for HDFS access.
    bool use_kerberos = false;
    std::string krb_keytab, krb_principal;
    if (!cloud_properties.empty()) {
        auto auth_it = cloud_properties.find("hadoop.security.authentication");
        if (auth_it != cloud_properties.end() && auth_it->second == "kerberos") {
            auto kt_it = cloud_properties.find("hadoop.security.keytab.file");
            auto pr_it = cloud_properties.find("hadoop.security.krb5.principal");
            if (kt_it != cloud_properties.end() && !kt_it->second.empty() &&
                pr_it != cloud_properties.end() && !pr_it->second.empty()) {
                use_kerberos = true;
                krb_keytab = kt_it->second;
                krb_principal = pr_it->second;
                hdfsBuilderConfSetStr(hdfs_builder, "hadoop.security.authentication", "kerberos");
                hdfsBuilderConfSetStr(hdfs_builder, "hadoop.security.keytab.file", krb_keytab.data());
                hdfsBuilderConfSetStr(hdfs_builder, "hadoop.security.krb5.principal", krb_principal.data());
            }
        }
    }

    // Save and restore KRB5CCNAME so each catalog can have its own Kerberos ticket
    // cache. This is safe because create_hdfs_fs_handle runs under HdfsFsCache::_lock.
    char* saved_krb5cc = nullptr;
    std::string per_catalog_krb5cc;
    if (use_kerberos) {
        saved_krb5cc = getenv("KRB5CCNAME");
        size_t hash_val = std::hash<std::string>{}(krb_keytab + ":" + krb_principal);
        per_catalog_krb5cc = "/tmp/starrocks_krb5cc_" + std::to_string(hash_val);
        setenv("KRB5CCNAME", ("FILE:" + per_catalog_krb5cc).c_str(), 1);
    }

    hdfs_client->hdfs_fs = hdfsBuilderConnect(hdfs_builder);

    if (use_kerberos) {
        if (saved_krb5cc != nullptr) {
            setenv("KRB5CCNAME", saved_krb5cc, 1);
        } else {
            unsetenv("KRB5CCNAME");
        }
    }

    if (hdfs_client->hdfs_fs == nullptr) {
        std::string err_detail = namenode;
        if (use_kerberos) {
            err_detail += " krb5_principal=" + krb_principal;
        }
        return Status::InternalError(strings::Substitute("fail to connect hdfs namenode, namenode=$0, err=$1",
                                                         err_detail, get_hdfs_err_msg()));
    }
    return Status::OK();
}"""

if old in content:
    content = content.replace(old, new)
    with open('/data/starrocks-build/starrocks-3.3.17/be/src/fs/hdfs/hdfs_fs_cache.cpp', 'w') as f:
        f.write(content)
    print('SUCCESS: File modified')
else:
    print('ERROR: Could not find the target text in the file')
    # Debug: show the actual content around where we expect the text
    import sys
    idx = content.find('Set for hdfs client hedged read')
    if idx >= 0:
        print('Found at position', idx)
        print(content[idx:idx+800])
    else:
        print('Could not find target section')

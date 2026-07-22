import shutil, os

# Create JAAS config for Krb5LoginModule
jaas_conf = '''HiveServer {
   com.sun.security.auth.module.Krb5LoginModule required
   useKeyTab=true
   storeKey=true
   useTicketCache=false
   keyTab="/data/deploy/keytabs/hive.service.keytab"
   principal="hive/localhost@SR.TEST"
   debug=true;
};
'''

jaas_path = '/data/starrocks-deploy/cluster_a/conf/jaas.conf'
with open(jaas_path, 'w') as f:
    f.write(jaas_conf)
print(f'Wrote {jaas_path}')

jaas_path_b = '/data/starrocks-deploy/cluster_b/conf/jaas.conf'
shutil.copy2(jaas_path, jaas_path_b)
print(f'Copied to {jaas_path_b}')

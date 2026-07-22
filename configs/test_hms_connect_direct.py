import subprocess

java = r"""
import org.apache.hadoop.hive.conf.HiveConf;
import org.apache.hadoop.hive.metastore.HiveMetaStoreClient;
import org.apache.hadoop.hive.metastore.api.MetaException;
import org.apache.hadoop.security.UserGroupInformation;
import org.apache.hadoop.conf.Configuration;

public class TestHMSConnect {
    public static void main(String[] args) throws Exception {
        System.setProperty("sun.security.krb5.debug", "true");
        System.setProperty("java.security.krb5.conf", "/opt/starrocks/fe/meta/krb5.conf");

        // Setup UGI with core-site.xml
        Configuration hadoopConf = new Configuration();
        hadoopConf.addResource(new org.apache.hadoop.fs.Path("/opt/starrocks/fe/conf/core-site.xml"));
        hadoopConf.set("hadoop.security.authentication", "kerberos");
        UserGroupInformation.setConfiguration(hadoopConf);

        // Login
        UserGroupInformation.loginUserFromKeytab(
            "hive/arm-hive@ARM.SR.TEST",
            "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab"
        );
        System.out.println("UGI LOGIN SUCCESS: " + UserGroupInformation.getCurrentUser());

        // Create HiveConf matching what StarRocks does
        HiveConf conf = new HiveConf();
        conf.addResource(hadoopConf);
        conf.set("hive.metastore.uris", "thrift://192.168.0.181:9083");
        conf.set("hive.metastore.sasl.enabled", "true");
        conf.set("hive.metastore.kerberos.principal", "hive/arm-hive@ARM.SR.TEST");
        conf.set("hive.metastore.client.kerberos.principal", "hive/arm-hive@ARM.SR.TEST");
        conf.set("hive.metastore.kerberos.keytab", "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab");
        conf.set("hadoop.security.authentication", "kerberos");

        System.out.println("Principal in conf: " + conf.getVar(HiveConf.ConfVars.METASTOREKERBEROSPRINCIPAL));

        // Try to connect
        HiveMetaStoreClient client = null;
        try {
            client = new HiveMetaStoreClient(conf);
            System.out.println("HMS CONNECT SUCCESS");
            System.out.println("Databases: " + client.getAllDatabases());
        } catch (Exception e) {
            System.out.println("HMS CONNECT FAILED: " + e.getMessage());
            e.printStackTrace(System.out);
        } finally {
            if (client != null) client.close();
        }
    }
}
"""

subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'tee', '/tmp/TestHMSConnect.java'], input=java, text=True, timeout=10)

cp = "/opt/starrocks/fe/lib/*"

r = subprocess.run(['docker', 'exec', 'sr-deploy', 'javac', '-cp', cp, '/tmp/TestHMSConnect.java', '-d', '/tmp'], capture_output=True, text=True, timeout=30)
print('javac:', r.stderr[:500] if r.returncode != 0 else 'OK')

if r.returncode == 0:
    r = subprocess.run(['docker', 'exec', 'sr-deploy', 'java',
        '-Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf',
        '-Dsun.security.krb5.debug=true',
        '-cp', f'/tmp:{cp}',
        'TestHMSConnect'], capture_output=True, text=True, timeout=60)
    print(r.stdout[:5000])
    if r.stderr:
        print('STDERR:', r.stderr[:500])

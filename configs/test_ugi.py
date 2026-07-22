import subprocess

java = r"""import org.apache.hadoop.security.UserGroupInformation;
import org.apache.hadoop.conf.Configuration;

public class TestUGI {
    public static void main(String[] args) throws Exception {
        System.setProperty("sun.security.krb5.debug", "true");
        System.setProperty("java.security.krb5.conf", "/opt/starrocks/fe/meta/krb5.conf");
        Configuration hadoopConf = new Configuration();
        hadoopConf.set("hadoop.security.authentication", "kerberos");
        UserGroupInformation.setConfiguration(hadoopConf);
        try {
            UserGroupInformation.loginUserFromKeytab(
                "hive/arm-hive@ARM.SR.TEST",
                "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab"
            );
            System.out.println("UGI LOGIN SUCCESS");
        } catch (Exception e) {
            System.out.println("UGI LOGIN FAILED: " + e);
            e.printStackTrace(System.out);
        }
    }
}
"""

# Write Java source
subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'tee', '/tmp/TestUGI.java'], input=java, text=True, timeout=10)

# Find hadoop jars
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'find', '/opt/starrocks', '-name', '*.jar', '-path', '*/hadoop*'], capture_output=True, text=True, timeout=15)
hadoop_jars = [j for j in r.stdout.strip().split('\n') if j]
print(f'Found {len(hadoop_jars)} hadoop jars')

cp = '/tmp:' + ':'.join(hadoop_jars)

r = subprocess.run(['docker', 'exec', 'sr-deploy', 'javac', '-cp', cp, '/tmp/TestUGI.java', '-d', '/tmp'], capture_output=True, text=True, timeout=30)
if r.returncode != 0:
    print('COMPILE ERROR:', r.stderr[:1000])
else:
    print('Compiled OK')
    r = subprocess.run(['docker', 'exec', 'sr-deploy', 'java', '-Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf', '-Dsun.security.krb5.debug=true', '-cp', cp, 'TestUGI'], capture_output=True, text=True, timeout=30)
    print(r.stdout[:5000])
    if r.stderr:
        print('STDERR:', r.stderr[:500])

import subprocess

java = r"""import javax.security.auth.login.LoginContext;
import javax.security.auth.login.LoginException;
import com.sun.security.auth.module.Krb5LoginModule;
import javax.security.auth.Subject;
import javax.security.auth.login.AppConfigurationEntry;
import javax.security.auth.login.Configuration;
import java.util.HashMap;
import java.util.Map;

public class TestKrb3 {
    public static void main(String[] args) {
        System.setProperty("sun.security.krb5.debug", "true");
        System.setProperty("java.security.krb5.conf", "/opt/starrocks/fe/meta/krb5.conf");
        Subject subject = new Subject();
        try {
            Configuration conf = new Configuration() {
                public AppConfigurationEntry[] getAppConfigurationEntry(String name) {
                    Map<String, String> options = new HashMap<>();
                    options.put("useKeyTab", "true");
                    options.put("keyTab", "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab");
                    options.put("principal", "hive/arm-hive@ARM.SR.TEST");
                    options.put("useTicketCache", "false");
                    options.put("doNotPrompt", "true");
                    options.put("storeKey", "true");
                    return new AppConfigurationEntry[]{
                        new AppConfigurationEntry(
                            Krb5LoginModule.class.getName(),
                            AppConfigurationEntry.LoginModuleControlFlag.REQUIRED,
                            options
                        )
                    };
                }
            };
            LoginContext lc = new LoginContext("test", subject, null, conf);
            lc.login();
            System.out.println("LOGIN SUCCESS");
            lc.logout();
        } catch (LoginException e) {
            System.out.println("LOGIN FAILED: " + e.getMessage());
            e.printStackTrace(System.out);
        } catch (Exception e) {
            System.out.println("ERROR: " + e);
            e.printStackTrace(System.out);
        }
    }
}
"""

subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'tee', '/tmp/TestKrb3.java'], input=java, text=True, timeout=10)
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'javac', '/tmp/TestKrb3.java', '-d', '/tmp'], capture_output=True, text=True, timeout=30)
if r.returncode != 0:
    print('COMPILE ERROR:', r.stderr[:1000])
else:
    r = subprocess.run(['docker', 'exec', 'sr-deploy', 'java', '-Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf', '-Dsun.security.krb5.debug=true', '-cp', '/tmp', 'TestKrb3'], capture_output=True, text=True, timeout=30)
    print(r.stdout[:5000])
    if r.stderr:
        print('STDERR:', r.stderr[:500])

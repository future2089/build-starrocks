import subprocess

java_source = r'''
import javax.security.auth.login.LoginContext;
import javax.security.auth.login.LoginException;
import com.sun.security.auth.module.Krb5LoginModule;
import javax.security.auth.Subject;
import java.util.HashMap;
import java.util.Map;

public class TestKrb3 {
    public static void main(String[] args) {
        System.setProperty("sun.security.krb5.debug", "true");
        System.setProperty("java.security.krb5.conf", "/opt/starrocks/fe/meta/krb5.conf");
        Subject subject = new Subject();
        try {
            LoginContext lc = new LoginContext("test", subject, null, (c) -> {
                Map<String, String> options = new HashMap<>();
                options.put("useKeyTab", "true");
                options.put("keyTab", "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab");
                options.put("principal", "hive/arm-hive@ARM.SR.TEST");
                options.put("useTicketCache", "false");
                options.put("doNotPrompt", "true");
                options.put("storeKey", "true");
                return new javax.security.auth.login.AppConfigurationEntry(
                    Krb5LoginModule.class.getName(),
                    javax.security.auth.login.AppConfigurationEntry.LoginModuleControlFlag.REQUIRED,
                    options
                );
            });
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
'''

# Write via docker exec
# Use Python to write the file inside the container
subprocess.run([
    'docker', 'exec', '-i', 'sr-deploy', 'sh', '-c', 'cat > /tmp/TestKrb3.java'
], input=java_source, text=True, timeout=10)

# Compile
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'javac', '/tmp/TestKrb3.java', '-d', '/tmp'], capture_output=True, text=True, timeout=30)
if r.returncode != 0:
    print('COMPILE ERROR:', r.stderr[:500])
    exit(1)

# Run
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'java', 
    '-Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf', 
    '-Dsun.security.krb5.debug=true', 
    '-cp', '/tmp', 'TestKrb3'], capture_output=True, text=True, timeout=30)
print(r.stdout[:5000])
if r.stderr:
    print('STDERR:', r.stderr[:500])

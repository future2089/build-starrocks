import subprocess

java_test = r'''
import javax.security.auth.login.LoginContext;
import javax.security.auth.login.LoginException;
import com.sun.security.auth.module.Krb5LoginModule;
import javax.security.auth.Subject;
import java.util.HashMap;
import java.util.Map;

public class TestKrb {
    public static void main(String[] args) {
        System.setProperty("sun.security.krb5.debug", "true");
        System.setProperty("java.security.krb5.conf", "/opt/starrocks/fe/meta/krb5.conf");
        
        Subject subject = new Subject();
        LoginContext lc = null;
        try {
            lc = new LoginContext("test", subject, null, (c) -> {
                Map<String, String> options = new HashMap<>();
                options.put("useKeyTab", "true");
                options.put("keyTab", "/opt/starrocks/fe/meta/keytabs/hive-arm.keytab");
                options.put("principal", "hive/arm-hive@ARM.SR.TEST");
                options.put("useTicketCache", "false");
                options.put("doNotPrompt", "true");
                options.put("storeKey", "true");
                options.put("isInitiator", "true");
                return new javax.security.auth.login.AppConfigurationEntry(
                    Krb5LoginModule.class.getName(),
                    javax.security.auth.login.AppConfigurationEntry.LoginModuleControlFlag.REQUIRED,
                    options
                );
            });
            lc.login();
            System.out.println("LOGIN SUCCESS");
            java.util.Set<Object> creds = subject.getPrivateCredentials();
            for (Object c : creds) {
                System.out.println("Cred: " + c);
            }
        } catch (LoginException e) {
            System.out.println("LOGIN FAILED: " + e.getMessage());
            e.printStackTrace(System.out);
        } catch (Exception e) {
            System.out.println("OTHER ERROR: " + e.getMessage());
            e.printStackTrace(System.out);
        } finally {
            if (lc != null) {
                try { lc.logout(); } catch (Exception e) {}
            }
        }
    }
}
'''

# Write to 211 host
r = subprocess.run(
    "cat > /tmp/TestKrb.java",
    shell=True, capture_output=True, text=True, timeout=5, 
    input=java_test
)

# docker cp to container and compile/run
r = subprocess.run(
    "docker cp /tmp/TestKrb.java sr-deploy:/tmp/TestKrb.java && docker exec sr-deploy javac /tmp/TestKrb.java -d /tmp 2>&1",
    shell=True, capture_output=True, text=True, timeout=30
)
print('compile:', r.stdout.strip()[:500], r.stderr.strip()[:500] if r.stderr else '')

r = subprocess.run(
    "docker exec sr-deploy java -Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf -Dsun.security.krb5.debug=true -cp /tmp TestKrb 2>&1",
    shell=True, capture_output=True, text=True, timeout=30
)
print('Output:')
print(r.stdout.strip()[:3000])
if r.stderr.strip():
    print('Stderr:', r.stderr.strip()[:1000])

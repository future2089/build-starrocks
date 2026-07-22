import subprocess

# Write a simple Java test for Kerberos login
java_test = '''
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
            System.out.println("LOGIN SUCCESS!");
            System.out.println("Subject: " + subject);
        } catch (LoginException e) {
            System.out.println("LOGIN FAILED: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (lc != null) {
                try { lc.logout(); } catch (Exception e) {}
            }
        }
    }
}
'''

# Write the test file into the container
r = subprocess.run(
    "docker exec sr-deploy bash -c 'cat > /tmp/TestKrb.java'",
    shell=True, capture_output=True, text=True, timeout=10
)
# Need to write via docker cp or heredoc
# Let's write to host and then docker cp

import tempfile
import os

tmpfile = '/tmp/TestKrb.java'
with open(tmpfile, 'w') as f:
    f.write(java_test)

r = subprocess.run(
    ['docker', 'cp', tmpfile, 'sr-deploy:/tmp/TestKrb.java'],
    capture_output=True, text=True, timeout=10
)
print('docker cp:', r.stdout.strip(), r.stderr.strip()[:200] if r.stderr else 'OK')

# Compile
r = subprocess.run(
    "docker exec sr-deploy javac /tmp/TestKrb.java -d /tmp",
    shell=True, capture_output=True, text=True, timeout=30
)
print('javac:', r.stdout.strip(), r.stderr.strip()[:500] if r.stderr else 'OK')

# Run
r = subprocess.run(
    "docker exec sr-deploy java -Djava.security.krb5.conf=/opt/starrocks/fe/meta/krb5.conf -Dsun.security.krb5.debug=true -cp /tmp TestKrb 2>&1",
    shell=True, capture_output=True, text=True, timeout=30
)
out = r.stdout.strip()
err = r.stderr.strip()
print('STDOUT:', out[:2000])
if err:
    print('STDERR:', err[:2000])

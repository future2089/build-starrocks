import javax.security.auth.login.*;
import com.sun.security.auth.module.Krb5LoginModule;
import java.util.Map;
import java.util.HashMap;
import javax.security.auth.Subject;
import java.security.PrivilegedAction;

public class TestKrb {
    public static void main(String[] args) throws Exception {
        System.setProperty("java.security.krb5.conf", args[0]);
        System.setProperty("sun.security.krb5.debug", "true");

        Krb5LoginModule module = new Krb5LoginModule();
        Subject subject = new Subject();
        Map<String, String> options = new HashMap<>();
        options.put("keyTab", args[1]);
        options.put("principal", args[2]);
        options.put("storeKey", "true");
        options.put("doNotPrompt", "true");
        options.put("useKeyTab", "true");
        options.put("isInitiator", "true");
        options.put("debug", "true");

        module.initialize(subject, null, new HashMap<String, Object>(), options);
        boolean ok = module.login();
        System.out.println("LOGIN: " + ok);
        if (ok) {
            module.commit();
            System.out.println("SUBJECT: " + subject);
        }
    }
}

import subprocess
# Check HMS Kerberos setup
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm bash -c "cat /data/package/apache-hive-3.1.3-bin/conf/hive-site.xml 2>/dev/null; echo ===; cat /etc/krb5.conf 2>/dev/null | head -30; echo ===; klist -k /etc/hive.keytab 2>/dev/null || klist -k /data/package/*.keytab 2>/dev/null || find / -name \"*.keytab\" -type f 2>/dev/null | head -5"'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:3000] or "(empty)")
print(r.stderr.strip()[:300] if r.stderr else '')

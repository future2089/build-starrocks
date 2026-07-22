import subprocess

script = r"""echo "=== hive-site.xml (Kerberos config) ==="
grep -i 'kerberos\|sasl\|principal\|keytab\|authentication\|authorization' /data/package/apache-hive-3.1.3-bin/conf/hive-site.xml 2>/dev/null || echo "(none)"

echo "=== /etc/krb5.conf ==="
cat /etc/krb5.conf 2>/dev/null || echo "(no /etc/krb5.conf)"

echo "=== keytabs ==="
find / -name "*.keytab" -type f 2>/dev/null | head -5
for kt in $(find / -name "*.keytab" -type f 2>/dev/null | head -3); do
    klist -k "$kt" 2>/dev/null | head -5
done

echo "=== HMS properties ==="
grep -i 'auth\|kerberos' /data/deploy/hadoop-conf/core-site.xml 2>/dev/null || echo "(no core-site.xml)"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_hms_kerb.sh'],
    input=script, text=True, capture_output=True, timeout=10
)

r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_hms_kerb.sh'],
    capture_output=True, text=True, timeout=20
)
print(r2.stdout.strip()[:3000] or "(empty)")
print("STDERR:", r2.stderr.strip()[:300] if r2.stderr else '')

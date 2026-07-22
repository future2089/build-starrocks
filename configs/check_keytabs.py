import subprocess

script = r"""echo "=== FE keytab ==="
ls -la /opt/starrocks/fe/meta/*.keytab 2>/dev/null
echo "=== FE krb5.conf ==="
cat /opt/starrocks/fe/meta/krb5.conf 2>/dev/null | head -20
echo "=== host HMS keytab ==="
ls -la /etc/security/keytabs/hive.service.keytab 2>/dev/null
echo "=== 181 host keytab ==="
ls -la /etc/security/keytabs/ 2>/dev/null
echo "=== Container HMS keytab ==="
docker exec hadoop-arm ls -la /etc/hive.keytab /etc/hdfs.keytab 2>/dev/null
echo "=== 181 /etc/krb5.conf ==="
cat /etc/krb5.conf 2>/dev/null | head -20
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_keytabs.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'bash < /tmp/check_keytabs.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

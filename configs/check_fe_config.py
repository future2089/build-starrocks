import subprocess

script = r"""echo "=== FE krb5.conf ==="
cat /opt/starrocks/fe/meta/krb5.conf 2>/dev/null
echo "=== FE conf ==="
grep -i "arm\|keytab\|kerberos\|krb5" /opt/starrocks/fe/conf/fe.conf 2>/dev/null | head -20
echo "=== FE meta keytabs ==="
ls -la /opt/starrocks/fe/meta/*.keytab 2>/dev/null || echo "(no keytabs in meta)"
echo "=== Check FE log for hive_arm ==="
grep -i "hive_arm\|kerberos.*login\|Unable to instantiate" /opt/starrocks/fe/log/fe.log 2>/dev/null | tail -5
echo "=== Check FE log for keytab ==="
grep -i "keytab\|principal\|loginUserFromKeytab\|starrocks-arm" /opt/starrocks/fe/log/fe.log 2>/dev/null | tail -10
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_fe_config.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'bash < /tmp/check_fe_config.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

import subprocess
script = r"""export KRB5CCNAME=/tmp/krb5_check
echo "=== Check hive principal ==="
kadmin.local -q "listprincs" 2>/dev/null | grep -i "hive\|arm-query\|starrocks" | head -10
echo "=== Keytab on host 181 for hive ==="
ls -la /etc/hive.keytab /etc/security/keytabs/hive.service.keytab /data/bigdata/apache-hive-3.1.3-bin/conf/*.keytab 2>/dev/null || echo "no keytabs found"
echo "=== Check which keytab HMS pid 860699 uses ==="
cat /proc/860699/cmdline | tr '\0' '\n' | grep -i "keytab\|principal" | head -5
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_princ.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_princ.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

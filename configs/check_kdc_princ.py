import subprocess
script = r"""echo "=== KDC inside container ==="
docker exec hadoop-arm bash -c 'ps aux | grep -i "krb5\|kdc\|kadmin" | grep -v grep'
echo "=== kadmin.local list principals ==="
docker exec hadoop-arm bash -c 'kadmin.local -q "listprincs" 2>/dev/null' | head -30
echo "=== Check /etc/hive.keytab ==="
docker exec hadoop-arm bash -c 'klist -k /etc/hive.keytab 2>/dev/null'
echo "=== Check /etc/hdfs.keytab ==="
docker exec hadoop-arm bash -c 'klist -k /etc/hdfs.keytab 2>/dev/null'
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_kdc_princ.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_kdc_princ.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

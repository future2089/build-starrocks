import subprocess
script = r"""grep -iE "hive_arm|hive-arm|Unable to instantiate|loginUserFromKeytab|LoginException|KrbException|Connected to|connectToServer|thrift.*181|Failed to connect|Kerberos login|principal.*arm|Successfully logged" /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null | tail -30
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/grep_fe2.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/grep_fe2.sh'], capture_output=True, text=True, timeout=10)
print(r2.stdout.strip()[:3000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

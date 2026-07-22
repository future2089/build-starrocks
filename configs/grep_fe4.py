import subprocess
script = r"""grep -iE "Connected to|connectToServer|success|StarRocksConnectorException|hive_arm|hive-arm|MetaException|Thrift connection|thrift.*9083|port.*9083" /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null | head -20
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/grep_fe4.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/grep_fe4.sh'], capture_output=True, text=True, timeout=10)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

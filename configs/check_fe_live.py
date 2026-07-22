import subprocess
script = r"""echo "=== FE process start ==="
ps -p 2634709 -o lstart=,etime=
echo "=== Check if fe.out has recent new content ==="
ls -la /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null
echo "=== Looking for success/error after SASL ==="
grep -E "ConnectException|Connected to|Failed|catalog.*arm|error|Error" /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null | tail -10
echo "=== Check internal log ==="
tail -20 /proc/2634709/root/opt/starrocks/fe/log/fe.internal.log 2>/dev/null
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_fe_live.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_fe_live.sh'], capture_output=True, text=True, timeout=10)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

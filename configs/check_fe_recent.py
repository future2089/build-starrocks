import subprocess
script = r"""echo "=== FE process start time ==="
ps -p 2634709 -o lstart=,etime=
echo "=== fe.out recent lines ==="
tail -50 /proc/2634709/root/opt/starrocks/fe/log/fe.out 2>/dev/null
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_fe_recent.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_fe_recent.sh'], capture_output=True, text=True, timeout=10)
print(r2.stdout.strip()[:2500] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

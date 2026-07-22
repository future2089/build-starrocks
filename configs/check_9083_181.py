import subprocess
script = r"""echo "=== Port 9083 on 181 ==="
ss -tlnp 2>/dev/null | grep 9083 || netstat -tlnp 2>/dev/null | grep 9083 || echo "NO TOOL"
echo "=== Host HMS process ==="
ps aux | grep "[m]etastore" | grep -v grep | grep -v "container\|docker\|hadoop-arm" | head -3
echo "=== Check all processes on 9083 ==="
fuser 9083/tcp 2>/dev/null || echo "fuser not available"
echo "=== Try connecting ==="
timeout 3 bash -c 'echo "" > /dev/tcp/192.168.0.181/9083' 2>&1 && echo "CONNECT OK" || echo "CONNECTION REFUSED"
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/check_9083_181.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/check_9083_181.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:1500] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

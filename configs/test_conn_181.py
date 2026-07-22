import subprocess
script = r"""echo "=== Test TCP to 181:9083 from 211 ==="
timeout 3 bash -c 'echo "test" | nc -w 2 192.168.0.181 9083' 2>&1 && echo "CONNECT OK" || echo "FAILED"
echo "=== Test with /dev/tcp ==="
timeout 3 bash -c 'exec 3<>/dev/tcp/192.168.0.181/9083; echo "CONNECT OK"; exec 3>&-' 2>&1 || echo "/dev/tcp FAILED"
echo "=== Check iptables on 211 ==="
iptables -L -n 2>/dev/null | grep -E "REJECT|DROP|181" | head -5 || echo "(no iptables or no rules)"
echo "=== Check connectivity to 181 ==="
ping -c1 -W2 192.168.0.181 2>&1 | head -2
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/test_conn_181.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/test_conn_181.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:1500] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

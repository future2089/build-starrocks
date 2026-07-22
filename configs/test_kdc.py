import subprocess
script = r"""echo "=== Test TCP to 181:88 from 211 ==="
timeout 3 bash -c 'exec 3<>/dev/tcp/192.168.0.181/88 && echo "TCP OK" || echo "TCP FAIL"'
echo "=== Test TCP to 181:88 from inside hadoop-arm container ==="
sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 'timeout 3 bash -c "exec 3<>/dev/tcp/127.0.0.1/88 && echo KDC OK || echo KDC FAIL"'
echo "=== Check KDC service on 181 (as host) ==="
sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 'ps aux | grep "[k]rb5kdc\|kadmind" | grep -v defunct'
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/test_kdc.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/test_kdc.sh'], capture_output=True, text=True, timeout=30)
print(r2.stdout.strip()[:1000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:300])

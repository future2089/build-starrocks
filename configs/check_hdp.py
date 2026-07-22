import subprocess

script = r"""echo "=== HDP HDFS ports ==="
ss -tlnp 2>/dev/null | grep -E "8020|50070|50075|9000" || netstat -tlnp 2>/dev/null | grep -E "8020|50070|50075|9000" || echo "no tools"
echo "=== HDP processes ==="
ps aux | grep -E "[N]ame[N]ode|[D]ata[N]ode|[R]esource[M]anager|[N]ode[M]anager|hdfs" | grep -v "apache-hive\|hive" | grep -v grep | head -10
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_hdp.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'bash < /tmp/check_hdp.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

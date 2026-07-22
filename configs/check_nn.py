import subprocess

script = r"""echo "=== All Java processes ==="
ps aux | grep -i java | grep -v grep | grep -v "usr/hdp"
echo "=== Check HDFS web UI ==="
curl -s --connect-timeout 3 http://localhost:50070/webhdfs/v1/?op=LISTSTATUS 2>&1 | head -5 || echo "HDFS web UI NOT RESPONDING"
echo "=== Check Hadoop services ==="
ps aux | grep -E "[N]ame[N]ode|[D]ata[N]ode|[S]econdary[N]ame[N]ode|[J]ournal[N]ode" | grep -v grep | head -5
echo "=== /tmp/hadoop/name ==="
ls -la /tmp/hadoop/name/current/ 2>/dev/null | head -5 || echo "(no name dir)"
echo "=== Check NN port 8020 ==="
ss -tlnp 2>/dev/null | grep 8020 || netstat -tlnp 2>/dev/null | grep 8020 || echo "NN 8020 NOT LISTENING"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_nn.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/check_nn.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

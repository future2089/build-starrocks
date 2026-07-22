import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH

echo "=== Check available user switching ==="
which su 2>/dev/null || echo "no su"
which runuser 2>/dev/null || echo "no runuser"
which sudo 2>/dev/null || echo "no sudo"
echo "=== Start NN manually ==="
nohup $HADOOP_HOME/bin/hdfs namenode > /tmp/hadoop-logs/namenode.log 2>&1 &
echo "NN PID=$!"
sleep 8
echo "=== Check NN process ==="
ps aux | grep "[N]ame[N]ode" | grep -v grep | head -2
echo "=== Check NN port ==="
ss -tlnp 2>/dev/null | grep 8020 || netstat -tlnp 2>/dev/null | grep 8020 || echo "NN NOT LISTENING"
echo "=== NN log tail ==="
tail -5 /tmp/hadoop-logs/namenode.log 2>/dev/null
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/start_nn.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/start_nn.sh'],
    capture_output=True, text=True, timeout=30
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

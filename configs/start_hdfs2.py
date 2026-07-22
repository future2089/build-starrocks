import subprocess

script = r"""export HADOOP_HOME=/data/package/hadoop-3.3.6
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HADOOP_LOG_DIR=/tmp/hadoop-logs
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH

echo "1. Kill any stale processes"
for pid in $(ps aux | grep -E "[N]ame[N]ode|[D]ata[N]ode" | awk '{print $2}'); do
  kill -9 $pid 2>/dev/null
done
sleep 2

echo "2. Start HDFS"
$HADOOP_HOME/sbin/start-dfs.sh 2>&1 | tail -10

echo "3. Wait and check"
sleep 8
ps aux | grep -E "[N]ame[N]ode|[D]ata[N]ode" | grep -v grep | head -5

echo "4. Check ports"
ss -tlnp 2>/dev/null | grep -E "8020|50070|50075" || echo "(checking netstat)"
netstat -tlnp 2>/dev/null | grep -E "8020|50070|50075" || echo "NO PORTS"

echo "---DONE---"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/start_hdfs2.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec -i hadoop-arm bash < /tmp/start_hdfs2.sh'],
    capture_output=True, text=True, timeout=60
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

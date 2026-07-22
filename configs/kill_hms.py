import subprocess

script = r"""echo "=== Processes listening on 9083 ==="
ss -tlnp | grep 9083
echo ""
echo "=== All metastore processes ==="
ps aux | grep -i "[m]etastore"
echo ""
echo "=== Force kill all ==="
for pid in $(ps aux | grep -i "[m]etastore" | awk '{print $2}'); do
  echo "Killing PID $pid..."
  kill -9 $pid 2>/dev/null
  sleep 1
done
echo "=== After kill ==="
ps aux | grep -i "[m]etastore" || echo "(none)"
echo "=== Port 9083 ==="
ss -tlnp | grep 9083 || echo "PORT FREE"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm bash -c "ss -tlnp | grep 9083; echo ---; ps aux | grep -i metastore"'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:1000] or "(empty)")
print("ERR:", r.stderr.strip()[:200] if r.stderr else '')

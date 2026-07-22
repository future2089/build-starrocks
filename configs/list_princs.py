import subprocess
script = r"""echo "=== KDC principals ==="
sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 'kadmin.local -q "listprincs" 2>&1' | grep -v "WARNING\|password\|^$" | head -30
"""
r = subprocess.run(['ssh', 'root@192.168.0.211', 'cat>/tmp/list_princs.sh'], input=script, text=True, timeout=10)
r2 = subprocess.run(['ssh', 'root@192.168.0.211', 'bash /tmp/list_princs.sh'], capture_output=True, text=True, timeout=15)
print(r2.stdout.strip()[:2000] or "(empty)")
if r2.stderr.strip(): print("ERR:", r2.stderr.strip()[:200])

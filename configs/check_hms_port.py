import subprocess
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm netstat -tlnp 2>/dev/null | grep 9083'],
    capture_output=True, text=True, timeout=15
)
print("Port 9083:", r.stdout.strip() or "(not listening)")

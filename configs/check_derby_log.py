import subprocess

# Check Derby log
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm tail -30 /derby.log'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000] or "(empty)")

# Also check the hadoop-arm network connectivity
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'timeout 5 bash -c "echo > /dev/tcp/192.168.0.181/9083 && echo HMS_PORT_OK || echo FAIL"'],
    capture_output=True, text=True, timeout=10
)
print("\nPort check from 211:", r2.stdout.strip())

import subprocess
# Check derby.log for the actual error
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm grep -i "error\|exception\|XJ040\|XJ041\|cannot.*create" /derby.log 2>/dev/null | tail -15'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000] or "(empty)")

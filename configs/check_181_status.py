import subprocess

# SSH to 181 via 211 and check status
r = subprocess.run(
    "sshpass -p 'Thinker@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.0.181 'hostname; docker ps --format table; echo ---PORTS---; ss -tlnp | head -30' 2>&1",
    shell=True, capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000])
print(r.stderr.strip()[:500] if r.stderr else '')

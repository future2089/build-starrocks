import subprocess, json

# Get all running containers with their PIDs
result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True)
container_ids = result.stdout.strip().split()

for cid in container_ids:
    insp = subprocess.run(['docker', 'inspect', cid], capture_output=True, text=True)
    try:
        data = json.loads(insp.stdout)
        for c in data:
            pid = c['State']['Pid']
            name = c['Name'].lstrip('/')
            print(f'{cid[:12]} {pid:>8} {name}')
    except:
        pass

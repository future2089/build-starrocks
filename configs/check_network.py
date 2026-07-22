import subprocess

# Check connectivity from sr-deploy to 181
r = subprocess.run(
    ['docker', 'exec', 'sr-deploy', 'python3', '-c', 
     'import socket;s=socket.socket();s.settimeout(3);s.connect(("192.168.0.181",9083));s.close();print("9083 OPEN")'],
    capture_output=True, text=True, timeout=10
)
print(r.stdout.strip())
print(r.stderr.strip()[:200] if r.stderr else '')

# Check if HMS is running on 181
r = subprocess.run(
    ['docker', 'exec', 'hadoop-arm', 'ps', 'aux'],
    capture_output=True, text=True, timeout=10
)
print('\nHMS processes on 181:')
for line in r.stdout.strip().split('\n'):
    if 'hive' in line.lower() or 'metastore' in line.lower():
        print(line[:200])

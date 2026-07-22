import subprocess

# Check connectivity from sr-deploy to 181:9083
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'python3', '-c', '''
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("192.168.0.181", 9083))
    s.close()
    print("9083 OPEN")
except Exception as e:
    print(f"9083 CLOSED: {e}")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("192.168.0.181", 8020))
    s.close()
    print("8020 OPEN")
except Exception as e:
    print(f"8020 CLOSED: {e}")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5)
    s.connect(("192.168.0.181", 88))
    s.send(b"test")
    print("88 UDP reachable")
except Exception as e:
    print(f"88 UDP error: {e}")
'''], capture_output=True, text=True, timeout=20)

print(r.stdout.strip())
print(r.stderr.strip()[:200] if r.stderr else '')

import socket

open_ports = []
for port in range(1, 65535, 1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect(('192.168.0.181', port))
        s.close()
        open_ports.append(port)
        print(f'{port} OPEN')
    except:
        pass

print(f'\nOpen ports: {open_ports}')

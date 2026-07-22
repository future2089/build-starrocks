import socket

for port in range(9000, 9100):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(('192.168.0.181', port))
        s.close()
        print(f'{port} OPEN')
    except:
        pass

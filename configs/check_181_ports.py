import socket
for port in [9083, 8020, 9866, 10000]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(('192.168.0.181', port))
        s.close()
        print(f'{port} OPEN')
    except Exception as e:
        print(f'{port} CLOSED: {e}')

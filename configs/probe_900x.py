import socket

for port in [9000, 9001]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(('192.168.0.181', port))
        s.send(b'GET / HTTP/1.0\r\n\r\n')
        data = s.recv(100)
        s.close()
        print(f'{port}: {repr(data)}')
    except Exception as e:
        print(f'{port}: {e}')

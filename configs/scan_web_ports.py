import socket

ports = [80, 443, 8080, 8443, 9001, 9090, 3000, 7001, 8000, 8888, 8088, 10000, 10002]
for port in ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('192.168.0.181', port))
        s.close()
        print(f'{port} OPEN')
    except Exception:
        pass

import socket

ports = [8020, 9000, 9001, 9870, 9866, 9867, 9868, 10000, 9083, 9084, 9085, 10500, 11000, 15000, 19888, 8088, 8032, 19888, 50070, 50075]
for port in ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('192.168.0.181', port))
        s.close()
        print(f'{port} OPEN')
    except Exception as e:
        print(f'{port} closed')

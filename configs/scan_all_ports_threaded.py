import socket
import threading
import queue

open_ports = []
lock = threading.Lock()
port_queue = queue.Queue()

for port in range(1, 65535):
    port_queue.put(port)

def worker():
    while not port_queue.empty():
        try:
            port = port_queue.get(timeout=1)
        except queue.Empty:
            break
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(('192.168.0.181', port))
            s.close()
            with lock:
                open_ports.append(port)
                print(f'{port} OPEN')
        except Exception:
            pass
        port_queue.task_done()

threads = [threading.Thread(target=worker) for _ in range(50)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f'\nOpen ports: {sorted(open_ports)}')

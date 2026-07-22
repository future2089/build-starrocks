import urllib.request

for url in [
    'http://192.168.0.181:8265',
    'http://192.168.0.181:8670',
    'http://192.168.0.181:10001',
    'http://192.168.0.181:10002',
    'http://192.168.0.181:10075',
]:
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        print(f'{url}: {resp.status}')
        print(resp.read().decode('utf-8', errors='ignore')[:300])
    except Exception as e:
        print(f'{url}: {e}')

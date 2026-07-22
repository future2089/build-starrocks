import urllib.request
for url in ['http://192.168.0.181:9000', 'http://192.168.0.181:9001']:
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        print(f'{url}: {resp.status}')
        print(resp.read().decode('utf-8', errors='ignore')[:500])
    except Exception as e:
        print(f'{url}: {e}')

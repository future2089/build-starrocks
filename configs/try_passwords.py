import subprocess

passwords = ['root', 'admin', 'password', '123456', 'starrocks', 'StarRocks', 'openEuler', 'openeuler']

for pw in passwords:
    r = subprocess.run(
        f"sshpass -p '{pw}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 root@192.168.0.181 'hostname' 2>&1",
        shell=True, capture_output=True, text=True, timeout=10
    )
    out = r.stdout.strip()
    err = r.stderr.strip()
    print(f'Pass {pw}: {out} / {err[:100]}')
    if 'hadoop-arm' in out or 'openEuler' in out:
        print(f'FOUND: {pw}')
        break

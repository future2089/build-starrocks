import subprocess
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm find / -name "hive-site.xml" -path "*/conf/*" 2>/dev/null'],
    capture_output=True, text=True, timeout=15
)
print("hive-site.xml:", r.stdout.strip())

for path in r.stdout.strip().split('\n'):
    if not path:
        continue
    r2 = subprocess.run(
        ['ssh', 'root@192.168.0.211',
         'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
         f'docker exec hadoop-arm grep -i "javax.jdo\|derby\|connection.url\|metastore.db" {path} 2>/dev/null'],
        capture_output=True, text=True, timeout=15
    )
    print(f"\n=== {path} ===")
    print(r2.stdout.strip()[:1000] or "(no matching lines)")

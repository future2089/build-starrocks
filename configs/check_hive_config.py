import subprocess
# Check hive-site.xml content and metastore_db directory
r = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'docker exec hadoop-arm sh -c "head -30 /data/package/apache-hive-3.1.3-bin/conf/hive-site.xml; echo ===; ls -la /data/package/apache-hive-3.1.3-bin/metastore_db/ 2>/dev/null | head -5; echo ===; find / -name metastore_db -type d 2>/dev/null | head -3"'],
    capture_output=True, text=True, timeout=15
)
print(r.stdout.strip()[:2000] or "(empty)")
print(r.stderr.strip()[:200] if r.stderr else '')

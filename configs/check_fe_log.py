import subprocess

script = r"""cat /proc/2634709/root/opt/starrocks/fe/log/fe.log 2>/dev/null | grep -iE 'hive_arm|hive-arm|kerberos.*login|Unable to instantiate|keytab' | tail -20
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/check_fe_log.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'bash /tmp/check_fe_log.sh'],
    capture_output=True, text=True, timeout=10
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

import subprocess

# Add HADOOP_CONF_DIR to fe.conf
r = subprocess.run(
    ['docker', 'exec', 'sr-deploy', 'bash', '-c', 'echo "HADOOP_CONF_DIR=/opt/starrocks/fe/conf" >> /opt/starrocks/fe/conf/fe.conf'],
    capture_output=True, text=True, timeout=10
)
print('add HADOOP_CONF_DIR:', r.stderr[:200] if r.stderr else 'OK')

# Verify
r = subprocess.run(
    ['docker', 'exec', 'sr-deploy', 'tail', '-3', '/opt/starrocks/fe/conf/fe.conf'],
    capture_output=True, text=True, timeout=10
)
print(r.stdout)

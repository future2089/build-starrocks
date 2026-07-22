import subprocess
sql = 'SHOW DATABASES FROM hive_arm;'
r = subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e', sql], capture_output=True)
print('STDOUT:', r.stdout.decode())
print('STDERR:', r.stderr.decode()[:200] if r.stderr else 'NONE')
print('EXIT CODE:', r.returncode)

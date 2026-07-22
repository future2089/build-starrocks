import subprocess, os

# Add debug flag to fe.conf
args = ['docker', 'exec', '-i', 'sr-deploy', 'sh', '-c']
cmd = 'echo JAVA_OPTS_FOR_JDK_11="$JAVA_OPTS_FOR_JDK_11 -Dsun.security.krb5.debug=true" >> /opt/starrocks/fe/conf/fe.conf'
subprocess.run(args + [cmd], check=True)
print('Added krb5 debug to fe.conf')

# Kill old FE
subprocess.run(['docker', 'exec', 'sr-deploy', 'kill', '-9', '407418'], capture_output=True)
print('Killed old FE')

# Start new FE
subprocess.run(['docker', 'exec', '-d', 'sr-deploy', 'bash', '/opt/starrocks/fe/bin/start_fe.sh', '--daemon'], check=True)
print('Started new FE, waiting...')

import time
time.sleep(8)

# Check PID
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'sh', '-c', 'ps aux | grep [S]tarRocksFE | head -1 | awk "{print $2}"'], capture_output=True, text=True)
print('New FE PID:', r.stdout.strip())

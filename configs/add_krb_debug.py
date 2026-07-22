import subprocess

# Read current fe.conf
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'cat', '/opt/starrocks/fe/conf/fe.conf'], capture_output=True, text=True)
lines = r.stdout.split('\n')
new_lines = []
for line in lines:
    if line.startswith('JAVA_OPTS_FOR_JDK_11'):
        if 'krb5.debug' not in line:
            line = line.rstrip() + ' -Dsun.security.krb5.debug=true'
    new_lines.append(line)

new_content = '\n'.join(new_lines)

# Write back using a Python script inside the container
pycode = f'''
with open('/opt/starrocks/fe/conf/fe.conf', 'w') as f:
    f.write({repr(new_content)})
print('DONE')
'''
r = subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'python3', '-c', pycode], capture_output=True, text=True, timeout=10)
print(r.stdout, r.stderr)

# Verify
r = subprocess.run(['docker', 'exec', 'sr-deploy', 'grep', 'JAVA_OPTS', '/opt/starrocks/fe/conf/fe.conf'], capture_output=True, text=True)
print(r.stdout)

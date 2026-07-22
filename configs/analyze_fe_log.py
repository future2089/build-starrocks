import subprocess

# Get the last 5000 lines of fe.out
r = subprocess.run(
    ['docker', 'exec', 'sr-deploy', 'tail', '-n', '500', '/opt/starrocks/fe/log/fe.out'],
    capture_output=True, text=True, timeout=30
)

lines = r.stdout.split('\n')

# Find the last KRBError or Kerberos-related exception
for i in range(len(lines)-1, -1, -1):
    if 'KRBError' in lines[i] or 'Server not found' in lines[i] or 'Fail to create credential' in lines[i]:
        start = max(0, i-10)
        end = min(len(lines), i+30)
        print('\n'.join(lines[start:end]))
        break
else:
    # Find any Kerberos login failed error
    for i in range(len(lines)-1, -1, -1):
        if 'Kerberos login failed' in lines[i] or 'Unable to instantiate' in lines[i]:
            start = max(0, i-5)
            end = min(len(lines), i+20)
            print('\n'.join(lines[start:end]))
            break

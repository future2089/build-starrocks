import subprocess

# Use Python's kerberos test inside the container
py_code = '''
import os, sys

os.environ['KRB5_CONFIG'] = '/opt/starrocks/fe/meta/krb5.conf'
os.environ['JAVA_HOME'] = '/lib/jvm/default-java'

# Try to use subprocess to call kinit via the java keytool
# First, just check if we can resolve the KDC
import socket
try:
    # Try connecting to KDC on TCP 88
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('192.168.0.181', 88))
    s.close()
    print('TCP 88 REACHABLE')
except Exception as e:
    print(f'TCP 88 FAIL: {e}')

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5)
    s.connect(('192.168.0.181', 88))
    s.close()
    print('UDP 88 REACHABLE')
except Exception as e:
    print(f'UDP 88 FAIL: {e}')

# Test keytab read permission
kt = '/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'
try:
    d = open(kt, 'rb').read()
    print(f'KEYTAB READ OK: {len(d)} bytes')
except Exception as e:
    print(f'KEYTAB READ FAIL: {e}')
'''

subprocess.run(['docker', 'exec', '-i', 'sr-deploy', 'python3', '-c', py_code], timeout=15)

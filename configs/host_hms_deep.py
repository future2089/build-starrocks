import subprocess

script = r"""cat /usr/hdp/current/hive-metastore/conf/hive-site.xml | python3 -c "
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.stdin)
root = tree.getroot()
targets = ['javax.jdo.option.ConnectionURL', 'javax.jdo.option.ConnectionDriverName',
           'hive.metastore.kerberos.principal', 'hive.metastore.kerberos.keytab.file',
           'fs.defaultFS', 'hive.metastore.uris']
for prop in root.findall('property'):
    name = prop.find('name').text
    if name in targets:
        val = prop.find('value').text if prop.find('value') is not None else ''
        print(f'{name} = {val}')
"
echo "=== Test HMS connectivity ==="
python3 -c "
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
from hive_metastore import ThriftHiveMetastore
import socket
s = socket.socket()
s.settimeout(5)
try:
    s.connect(('192.168.0.181', 9083))
    print('Port 9083 OPEN')
except Exception as e:
    print(f'Port 9083: {e}')
finally:
    s.close()
" 2>&1 || echo "Python test not available"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/host_hms_deep.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'bash < /tmp/host_hms_deep.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:2000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

import subprocess

script = r"""CONF=/usr/hdp/current/hive-metastore/conf/hive-site.xml
echo "=== Full HMS config ==="
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$CONF')
root = tree.getroot()
for prop in root.findall('property'):
    name = prop.find('name').text
    val = prop.find('value').text if prop.find('value') is not None else ''
    print(f'{name}={val}')
" || grep -A1 '<name>' "$CONF" | grep -v -- '--' | paste - - | sed 's/.*<name>\(.*\)<\/name>.*<value>\(.*\)<\/value>.*/\1 = \2/' || echo "Parse failed"
"""

r = subprocess.run(
    ['ssh', 'root@192.168.0.211', 'cat > /tmp/host_hms_config.sh'],
    input=script, text=True, capture_output=True, timeout=10
)
r2 = subprocess.run(
    ['ssh', 'root@192.168.0.211',
     'sshpass -p Thinker@123 ssh -o StrictHostKeyChecking=no root@192.168.0.181 '
     'bash < /tmp/host_hms_config.sh'],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout.strip()[:3000] or "(empty)")
err = r2.stderr.strip()[:300] if r2.stderr else ''
if err: print("STDERR:", err)

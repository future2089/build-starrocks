import base64, os

path = '/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'
if not os.path.exists(path):
    print('FILE NOT FOUND')
    exit(1)

data = open(path, 'rb').read()
print('Size:', len(data), 'bytes')
print('B64 start:', base64.b64encode(data[:32]).decode())

expected_start = 'BQIAAABWAAIAC0FSTS5TUi5URVNUAAlzdGFycm9ja3MA'
actual_start = base64.b64encode(data[:18]).decode()
print('Expected start of: BQIAAABWAAIAC0FSTS5TUi5URVNUAAlzdGFycm9ja3MA')
print('Actual start:', actual_start)
if actual_start.startswith('BQIAAABWAAIAC0FST'):
    print('KEYTAB LOOKS CORRECT')
else:
    print('KEYTAB IS CORRUPTED!')

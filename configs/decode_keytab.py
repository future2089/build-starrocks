import base64, subprocess
b64 = """BQIAAABWAAIAC0FSTS5TUi5URVNUAAlzdGFycm9ja3MACWFybS1xdWVyeQAAAAFqXbmwAgASACB6
HD5/CtosBCceViku68Z44FIv7anap65W1AQisITRrgAAAAIAAABGAAIAC0FSTS5TUi5URVNUAAlz
dGFycm9ja3MACWFybS1xdWVyeQAAAAFqXbmwAgARABAke+g17bfv7r3EPEswmhmTAAAAAgAAAEYA
AgALQVJNLlNSLlRFU1QACXN0YXJyb2NrcwAJYXJtLXF1ZXJ5AAAAAWpdubACABcAEM4afOlexkQX
dzGFF6p2wggAAAACAAAAVgACAAtBUk0uU1IuVEVTVAAJc3RhcnJvY2tzAAlhcm0tcXVlcnkAAAAB
al25sAIAGgAgKRELSIVl998jyu3WPD+P8P9TODDHQkIN7wF+5kYRk4kAAAACAAAARgACAAtBUk0u
U1IuVEVTVAAJc3RhcnJvY2tzAAlhcm0tcXVlcnkAAAABal25sAIAGQAQ8aWduXLSkzh8vgRn6A6M
6QAAAAI="""
data = base64.b64decode(b64)
with open('/tmp/starrocks-arm.keytab', 'wb') as f:
    f.write(data)
print('KEYTAB SIZE:', len(data), 'bytes')
subprocess.run(['docker', 'cp', '/tmp/starrocks-arm.keytab', 'sr-deploy:/opt/starrocks/fe/meta/keytabs/starrocks-arm.keytab'], check=True)
print('COPIED INTO CONTAINER')

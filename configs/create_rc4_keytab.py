import subprocess

cmd = "ssh root@192.168.0.181 'echo ktadd -k /tmp/starrocks-arm-rc4.keytab -e arcfour-hmac:normal starrocks/arm-query@ARM.SR.TEST | kadmin.local && klist -ket /tmp/starrocks-arm-rc4.keytab'"
r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
print('STDOUT:', r.stdout)
print('STDERR:', r.stderr[:200])
print('RC:', r.returncode)

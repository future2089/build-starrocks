import subprocess

r = subprocess.run(
    "docker exec sr-deploy grep -E 'Server not found|acquireServiceCreds|krbtgt/SR.TEST|Krb5Context|server principal|sname is' /opt/starrocks/fe/log/fe.out | tail -10",
    shell=True, capture_output=True, text=True, timeout=30
)
print(r.stdout[:1000])

# Also check what principal is logged in the debug output before the error
r2 = subprocess.run(
    "docker exec sr-deploy grep -B5 'Fail to create credential' /opt/starrocks/fe/log/fe.out | tail -10",
    shell=True, capture_output=True, text=True, timeout=30
)
print('\n--- Before error ---')
print(r2.stdout[:1000])

import subprocess

# Get line numbers of arm-hive occurrences
r = subprocess.run(
    "docker exec sr-deploy grep -n 'arm-hive' /opt/starrocks/fe/log/fe.out",
    shell=True, capture_output=True, text=True, timeout=30
)
lines = r.stdout.strip().split('\n')
line_nums = [int(l.split(':')[0]) for l in lines if l]
print(f'Total arm-hive lines: {len(line_nums)}')
print(f'Last few line numbers: {line_nums[-10:]}')

# Read the last few lines of the log around the last arm-hive entry
last_line = line_nums[-1]
# Get from 100 lines before to 50 lines after the last arm-hive entry
start = max(1, last_line - 100)
r = subprocess.run(
    f"docker exec sr-deploy sed -n '{start},{last_line + 50}p' /opt/starrocks/fe/log/fe.out",
    shell=True, capture_output=True, text=True, timeout=30
)
print(f'\n--- Log around last arm-hive entry (lines {start}-{last_line + 50}) ---')
# Filter for meaningful lines
for line in r.stdout.strip().split('\n'):
    if any(kw in line for kw in ['arm-hive', 'Kerberos', 'Exception', 'Login', 'TGS', 'Credentials', 'fail', 'KrbAsReq', 'KrbAsRep', 'Krb5LoginModule', 'Caused by', 'ERROR', 'Error']):
        print(line[:200])

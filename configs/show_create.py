import subprocess

# Get full SHOW CREATE CATALOG output
r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     'SHOW CREATE CATALOG hive_arm;'],
    capture_output=True, text=True, timeout=15
)
output = r.stdout.strip()
# Unescape the escaped newlines
output = output.replace('\\n', '\n')
print(output[:2000])

# Also check what properties were actually stored - query catalog metadata
r2 = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-N', '-e',
     "SELECT * FROM information_schema.catalogs;"],
    capture_output=True, text=True, timeout=15
)
print("\n=== information_schema.catalogs ===")
for line in r2.stdout.split('\n')[:20]:
    print(line[:200])
print(r2.stderr.strip()[:500] if r2.stderr else '')

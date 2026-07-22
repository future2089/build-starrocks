import subprocess

r = subprocess.run(
    ['docker', 'exec', '-i', 'sr-deploy', 'mysql', '-h127.0.0.1', '-P9030', '-uroot', '-e', 'SHOW CATALOGS;'],
    capture_output=True, text=True, timeout=30
)
print(r.stdout.strip())
print(r.stderr.strip()[:500] if r.stderr else '')
